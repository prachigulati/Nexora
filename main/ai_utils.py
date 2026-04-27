import os
import re
import json
from typing import List, Dict, Any
from django.db.models import Sum
from sentence_transformers import SentenceTransformer, util
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from joblib import dump, load
from django.conf import settings
from main.models import Project

MODEL_PATH = os.path.join(settings.BASE_DIR, 'pitch_nlp_model.pkl')

# Lazy loading for heavy models to prevent worker timeout
_sbert_model = None
_paraphrase_model = None
_paraphrase_tokenizer = None

def get_sbert_model():
    """Lazy load the SBERT model"""
    global _sbert_model
    if _sbert_model is None:
        _sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _sbert_model

def get_paraphrase_model():
    """Lazy load the paraphrase model"""
    global _paraphrase_model
    if _paraphrase_model is None:
        from transformers import T5ForConditionalGeneration
        _paraphrase_model = T5ForConditionalGeneration.from_pretrained("ramsrigouthamg/t5_paraphraser")
    return _paraphrase_model

def get_paraphrase_tokenizer():
    """Lazy load the paraphrase tokenizer"""
    global _paraphrase_tokenizer
    if _paraphrase_tokenizer is None:
        from transformers import T5Tokenizer
        _paraphrase_tokenizer = T5Tokenizer.from_pretrained("ramsrigouthamg/t5_paraphraser")
    return _paraphrase_tokenizer


def train_pitch_classifier():
    projects = Project.objects.annotate(
        total_funding=Sum('transactions__amount_eth')
    ).filter(
        total_funding__isnull=False
    )

    texts = []
    labels = []

    for project in projects:
        total_funding = float(project.total_funding or 0)
        funding_goal = float(project.funding_goal or 1)

        is_successful = total_funding >= 0.5 * funding_goal

        combined_text = " ".join([
            project.description or "",
            project.problem or "",
            project.market or "",
            project.competition or "",
            project.category or "",
        ])

        texts.append(combined_text)
        labels.append(1 if is_successful else 0)

    if len(set(labels)) < 2:
        print("Not enough variation in success labels to train the model.")
        return

    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english', max_features=5000)),
        ('clf', LogisticRegression(max_iter=1000))
    ])

    X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42)
    pipeline.fit(X_train, y_train)

    dump(pipeline, MODEL_PATH)
    print("Model trained and saved as pitch_nlp_model.pkl")


def load_pitch_classifier():
    if os.path.exists(MODEL_PATH):
        return load(MODEL_PATH)
    else:
        return train_pitch_classifier()



def generate_suggestions(user_text):
    if not user_text:
        return []

    try:
        sbert_model = get_sbert_model()
        user_vec = sbert_model.encode(user_text, convert_to_tensor=True)
    except Exception as e:
        return [f"Encoding error: {str(e)}"]

    from django.db.models import Sum
    from decimal import Decimal

    successful = Project.objects.annotate(
        total_funding=Sum('transactions__amount_eth'),
    ).filter(
        total_funding__isnull=False,
        funding_goal__isnull=False
    )

    valid_projects = []
    for p in successful:
        try:
            total_funding = float(p.total_funding or 0)
            funding_goal = float(p.funding_goal or 1)
            if total_funding >= 0.5 * funding_goal:
                valid_projects.append(p)
        except Exception as e:
            continue

    base_texts = [
        ' '.join(filter(None, [p.description, p.problem, p.market, p.competition]))
        for p in valid_projects
        if any([p.description, p.problem, p.market, p.competition])
    ]

    if not base_texts:
        return ["Not enough successful project data to compare."]

    try:
        sbert_model = get_sbert_model()
        base_vecs = sbert_model.encode(base_texts, convert_to_tensor=True)
        similarity = util.pytorch_cos_sim(user_vec, base_vecs).max().item()
    except Exception as e:
        return [f"Similarity calculation error: {str(e)}"]

    suggestions = []

    if similarity < 0.45:
        suggestions.append("Your pitch is not aligned with successful patterns. Try being more specific and clear.")

    return suggestions




import torch

def rewrite_pitch(text):
    if not text or len(text.strip().split()) < 5:
        return "Please enter a longer or more detailed pitch."

    # Get models lazily
    paraphrase_model = get_paraphrase_model()
    paraphrase_tokenizer = get_paraphrase_tokenizer()

    # Format input for the model
    prompt = f"paraphrase: {text.lower()} </s>"
    encoding = paraphrase_tokenizer.encode_plus(
        prompt, padding="longest", return_tensors="pt"
    )

    input_ids, attention_mask = encoding["input_ids"], encoding["attention_mask"]

    try:
        # Generate paraphrased text
        outputs = paraphrase_model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_length=256,
            do_sample=True,
            top_k=50, 
            num_return_sequences=1,
            early_stopping=True
        )


        # Decode the output
        rewritten = paraphrase_tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Avoid same output
        if rewritten.strip().lower() == text.strip().lower():
            return "Try rephrasing or providing a longer pitch for better results."

        return rewritten

    except Exception as e:
        return f"Rewrite failed: {str(e)}"


def analyze_pitch_strength(text: str) -> Dict[str, Any]:
    """
    Analyze pitch text and provide comprehensive feedback
    """
    if not text or len(text.strip()) < 10:
        return {
            'score': 0,
            'word_count': 0,
            'feedback': ['Please provide more detailed information about your project.'],
            'suggestions': ['Add more specific details about your problem, solution, and market.']
        }
    
    # Basic text analysis
    words = text.split()
    word_count = len(words)
    char_count = len(text)
    
    # Calculate basic metrics
    avg_word_length = char_count / word_count if word_count > 0 else 0
    unique_words = len(set(words))
    vocabulary_richness = unique_words / word_count if word_count > 0 else 0
    
    # Initialize score
    score = 0
    feedback = []
    suggestions = []
    
    # Word count scoring (0-25 points)
    if word_count >= 50:
        score += 25
        feedback.append("Excellent word count - provides comprehensive information.")
    elif word_count >= 30:
        score += 20
        feedback.append("Good word count - covers key aspects.")
    elif word_count >= 20:
        score += 15
        feedback.append("Adequate word count - consider adding more details.")
    elif word_count >= 10:
        score += 10
        feedback.append("Basic word count - needs more elaboration.")
    else:
        score += 5
        feedback.append("Very brief - significantly more detail needed.")
        suggestions.append("Expand your description with more specific details.")
    
    # Vocabulary richness scoring (0-25 points)
    if vocabulary_richness >= 0.7:
        score += 25
        feedback.append("Excellent vocabulary diversity.")
    elif vocabulary_richness >= 0.5:
        score += 20
        feedback.append("Good vocabulary diversity.")
    elif vocabulary_richness >= 0.3:
        score += 15
        feedback.append("Adequate vocabulary - consider using more varied terms.")
    else:
        score += 10
        feedback.append("Limited vocabulary - consider using more diverse language.")
        suggestions.append("Use more varied and professional terminology.")
    
    # Content analysis (0-30 points)
    content_score = 0
    text_lower = text.lower()
    
    # Check for key elements
    if any(word in text_lower for word in ['problem', 'issue', 'challenge', 'need']):
        content_score += 10
        feedback.append("Good problem identification.")
    else:
        suggestions.append("Clearly state the problem you're solving.")
    
    if any(word in text_lower for word in ['solution', 'product', 'service', 'platform']):
        content_score += 10
        feedback.append("Good solution description.")
    else:
        suggestions.append("Describe your solution or product clearly.")
    
    if any(word in text_lower for word in ['market', 'industry', 'sector', 'customers']):
        content_score += 10
        feedback.append("Good market awareness.")
    else:
        suggestions.append("Include information about your target market.")
    
    score += content_score
    
    # Professional language scoring (0-20 points)
    professional_terms = ['innovative', 'technology', 'platform', 'solution', 'market', 'industry', 'customers', 'revenue', 'growth', 'partnership']
    professional_count = sum(1 for term in professional_terms if term in text_lower)
    
    if professional_count >= 5:
        score += 20
        feedback.append("Excellent use of professional terminology.")
    elif professional_count >= 3:
        score += 15
        feedback.append("Good use of professional language.")
    elif professional_count >= 1:
        score += 10
        feedback.append("Some professional terms used - consider more industry-specific language.")
    else:
        score += 5
        feedback.append("Limited professional terminology - consider industry-specific terms.")
        suggestions.append("Use more industry-specific and professional terminology.")
    
    # Ensure score doesn't exceed 100
    score = min(score, 100)
    
    # Add general suggestions based on score
    if score < 50:
        suggestions.extend([
            "Provide more specific details about your business model.",
            "Include information about your competitive advantage.",
            "Add details about your team and experience."
        ])
    elif score < 70:
        suggestions.extend([
            "Consider adding more quantitative data and metrics.",
            "Include information about your go-to-market strategy.",
            "Add details about your funding requirements and use of funds."
        ])
    else:
        suggestions.append("Consider adding specific metrics and success indicators.")
    
    return {
        'score': score,
        'word_count': word_count,
        'feedback': feedback,
        'suggestions': suggestions,
        'metrics': {
            'avg_word_length': round(avg_word_length, 2),
            'vocabulary_richness': round(vocabulary_richness, 3),
            'professional_terms': professional_count
        }
    }

def get_field_suggestions(field_name: str, current_value: str, other_fields: Dict[str, str]) -> Dict[str, Any]:
    """
    Get AI suggestions for specific project fields
    """
    suggestions = []
    template = ""
    
    # Field-specific suggestions
    if field_name == "description":
        if len(current_value) < 50:
            suggestions.append("Make your description more comprehensive - aim for at least 50 words.")
        if not any(word in current_value.lower() for word in ['platform', 'solution', 'product', 'service']):
            suggestions.append("Clearly describe what your product or service does.")
        template = "We are building [product/service] that [solves problem] for [target market]."
    
    elif field_name == "problem":
        if not any(word in current_value.lower() for word in ['problem', 'issue', 'challenge', 'pain']):
            suggestions.append("Clearly state the problem or pain point you're addressing.")
        if len(current_value) < 30:
            suggestions.append("Provide more context about the problem and its impact.")
        template = "Current solutions in [industry] fail to [specific problem], causing [negative impact]."
    
    elif field_name == "market":
        if not any(word in current_value.lower() for word in ['market', 'industry', 'sector', 'customers']):
            suggestions.append("Describe your target market and industry.")
        if not any(word in current_value.lower() for word in ['billion', 'million', 'growth', 'size']):
            suggestions.append("Include market size and growth potential.")
        template = "The [industry] market is valued at [size] with [growth rate] annual growth."
    
    elif field_name == "competition":
        if not any(word in current_value.lower() for word in ['competition', 'competitor', 'alternative']):
            suggestions.append("Address your competitive landscape.")
        if len(current_value) < 20:
            suggestions.append("Explain how you differentiate from existing solutions.")
        template = "While [competitors] exist, they lack [your unique advantage]."
    
    elif field_name == "details":
        if len(current_value) < 40:
            suggestions.append("Provide more technical or business details.")
        if not any(word in current_value.lower() for word in ['technology', 'team', 'experience', 'strategy']):
            suggestions.append("Include technical details, team info, or business strategy.")
        template = "Our solution leverages [technology/approach] with [team expertise] to deliver [benefit]."
    
    # Cross-field analysis
    combined_text = ' '.join([current_value] + list(other_fields.values()))
    if combined_text.strip():
        analysis = analyze_pitch_strength(current_value) if current_value else None
    else:
        analysis = None
    
    return {
        'suggestions': suggestions,
        'template': template,
        'analysis': analysis
    }

def enhance_project_creation_data(project_data: Dict[str, str]) -> Dict[str, Any]:
    """
    Enhance project creation data with AI analysis and suggestions
    """
    enhanced_data = {}
    
    # Analyze each field
    for field_name, field_value in project_data.items():
        if field_value and field_value.strip():
            analysis = analyze_pitch_strength(field_value)
            enhanced_data[field_name] = {
                'value': field_value,
                'analysis': analysis,
                'suggestions': get_field_suggestions(field_name, field_value, project_data)
            }
    
    # Overall analysis
    combined_text = ' '.join([v for v in project_data.values() if v])
    if combined_text.strip():
        enhanced_data['overall'] = analyze_pitch_strength(combined_text)
    
    # Cross-field insights
    enhanced_data['insights'] = []
    
    if project_data.get('problem') and project_data.get('description'):
        if 'solution' in project_data['description'].lower() and 'problem' in project_data['problem'].lower():
            enhanced_data['insights'].append("Good alignment between problem and solution descriptions.")
        else:
            enhanced_data['insights'].append("Consider better connecting your problem and solution descriptions.")
    
    if project_data.get('market') and project_data.get('problem'):
        if 'market' in project_data['market'].lower() and 'problem' in project_data['problem'].lower():
            enhanced_data['insights'].append("Market and problem descriptions are well-connected.")
        else:
            enhanced_data['insights'].append("Consider linking your market description to the problem you're solving.")
    
    return enhanced_data