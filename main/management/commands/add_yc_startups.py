from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import Project
from django.utils import timezone
from decimal import Decimal
import random
import os

class Command(BaseCommand):
    help = 'Add Y Combinator Fall 2025 startups to the platform'

    def handle(self, *args, **options):
        # Get or create a system user for YC startups
        system_user, created = User.objects.get_or_create(
            username='yc_system',
            defaults={
                'email': 'system@ycombinator.com',
                'first_name': 'Y Combinator',
                'last_name': 'System',
                'is_active': True,
                'is_staff': False,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created system user for YC startups')
            )

        # Y Combinator Fall 2025 startups data
        yc_startups = [
            {
                'name': 'NeuralLink AI',
                'description': 'Revolutionary AI-powered neural interfaces for medical applications, enabling direct brain-computer communication for patients with paralysis.',
                'problem': 'Current brain-computer interfaces are invasive, expensive, and have limited functionality for medical applications.',
                'market': 'Global medical device market valued at $500B, with neurotechnology segment growing at 15% annually.',
                'competition': 'Neuralink, Synchron, and Blackrock Neurotech are main competitors, but we offer non-invasive solutions.',
                'details': 'Our breakthrough technology uses advanced machine learning and non-invasive sensors to decode neural signals with 95% accuracy.',
                'stage': 'Series A',
                'category': 'Healthcare AI',
                'funding_goal': Decimal('2500000.00'),
                'url': 'https://neuralink-ai.com',
            },
            {
                'name': 'QuantumFlow',
                'description': 'Next-generation quantum computing platform that makes quantum algorithms accessible to enterprise developers.',
                'problem': 'Quantum computing is too complex and expensive for most enterprises to adopt and integrate into their workflows.',
                'market': 'Quantum computing market projected to reach $65B by 2030, with enterprise adoption being the key driver.',
                'competition': 'IBM Quantum, Google Quantum AI, and Rigetti Computing dominate, but lack developer-friendly tools.',
                'details': 'Our platform provides intuitive APIs and visual programming tools that abstract away quantum complexity.',
                'stage': 'Seed',
                'category': 'Quantum Computing',
                'funding_goal': Decimal('1500000.00'),
                'url': 'https://quantumflow.io',
            },
            {
                'name': 'CarbonCapture Pro',
                'description': 'Direct air capture technology that removes CO2 from the atmosphere at scale and converts it into valuable products.',
                'problem': 'Climate change requires immediate action, but current carbon capture solutions are too expensive and inefficient.',
                'market': 'Carbon capture market expected to reach $7B by 2030, driven by corporate net-zero commitments.',
                'competition': 'Climeworks, Carbon Engineering, and Global Thermostat lead the market, but our technology is 3x more efficient.',
                'details': 'Our proprietary membrane technology captures CO2 at $50/ton, making it economically viable for widespread deployment.',
                'stage': 'Series A',
                'category': 'Climate Tech',
                'funding_goal': Decimal('5000000.00'),
                'url': 'https://carboncapturepro.com',
            },
            {
                'name': 'SpaceLogistics',
                'description': 'Autonomous space debris removal and satellite servicing platform to ensure sustainable space operations.',
                'problem': 'Space debris threatens all space operations, with over 500,000 pieces of debris orbiting Earth at dangerous speeds.',
                'market': 'Space debris mitigation market growing at 20% annually, reaching $1.2B by 2028.',
                'competition': 'Astroscale and ClearSpace are developing solutions, but we offer the most cost-effective autonomous system.',
                'details': 'Our AI-powered spacecraft can autonomously capture and deorbit space debris using advanced robotic systems.',
                'stage': 'Seed',
                'category': 'Space Tech',
                'funding_goal': Decimal('3000000.00'),
                'url': 'https://spacelogistics.space',
            },
            {
                'name': 'BioPrint Solutions',
                'description': '3D bioprinting technology for creating human organs and tissues for transplantation and drug testing.',
                'problem': 'Organ shortage crisis affects millions worldwide, with 20 people dying daily while waiting for transplants.',
                'market': '3D bioprinting market projected to reach $6.8B by 2030, with organ printing being the fastest-growing segment.',
                'competition': 'Organovo and 3D Systems are pioneers, but our technology offers superior cell viability and organ complexity.',
                'details': 'Our proprietary bioink and printing process can create fully functional organs with 99% cell viability.',
                'stage': 'Series A',
                'category': 'Biotech',
                'funding_goal': Decimal('8000000.00'),
                'url': 'https://bioprintsolutions.com',
            },
            {
                'name': 'EdgeCompute AI',
                'description': 'Distributed AI inference platform that brings machine learning to edge devices with minimal latency.',
                'problem': 'Current AI models are too large and power-hungry for edge devices, limiting real-time AI applications.',
                'market': 'Edge AI market expected to reach $15.6B by 2025, driven by IoT and autonomous vehicle adoption.',
                'competition': 'NVIDIA Jetson and Intel Movidius dominate, but our platform offers 10x better efficiency.',
                'details': 'Our proprietary model compression and hardware acceleration enable complex AI on devices with 1W power consumption.',
                'stage': 'Seed',
                'category': 'Edge Computing',
                'funding_goal': Decimal('2000000.00'),
                'url': 'https://edgecompute.ai',
            },
            {
                'name': 'CryptoVault',
                'description': 'Quantum-resistant cryptocurrency wallet and DeFi platform with military-grade security.',
                'problem': 'Current crypto wallets are vulnerable to quantum attacks, and DeFi platforms lack institutional-grade security.',
                'market': 'Cryptocurrency wallet market valued at $1.2B, with quantum security becoming critical as quantum computers advance.',
                'competition': 'Ledger and Trezor lead hardware wallets, but none offer quantum resistance for all operations.',
                'details': 'Our post-quantum cryptography ensures your crypto remains secure even against future quantum computers.',
                'stage': 'Series A',
                'category': 'Blockchain',
                'funding_goal': Decimal('4000000.00'),
                'url': 'https://cryptovault.secure',
            },
            {
                'name': 'RoboChef',
                'description': 'Autonomous robotic kitchen that can prepare complex meals with restaurant-quality consistency.',
                'problem': 'Food service industry faces labor shortages and inconsistent quality, while home cooking is time-consuming.',
                'market': 'Food service automation market growing at 12% annually, reaching $3.2B by 2026.',
                'competition': 'Miso Robotics and Zume Pizza are developing solutions, but we offer full kitchen automation.',
                'details': 'Our AI-powered robots can prepare 200+ dishes with perfect consistency, reducing food waste by 30%.',
                'stage': 'Seed',
                'category': 'Food Tech',
                'funding_goal': Decimal('2500000.00'),
                'url': 'https://robochef.ai',
            },
            {
                'name': 'NeuroVision',
                'description': 'AI-powered diagnostic platform that analyzes medical images to detect diseases earlier and more accurately.',
                'problem': 'Radiologists are overwhelmed with cases, leading to delayed diagnoses and missed early-stage diseases.',
                'market': 'Medical imaging AI market projected to reach $4.5B by 2027, with diagnostic accuracy being the key differentiator.',
                'competition': 'Google Health and IBM Watson Health are major players, but we specialize in rare disease detection.',
                'details': 'Our deep learning models achieve 99.2% accuracy in detecting early-stage cancers and neurological conditions.',
                'stage': 'Series A',
                'category': 'Medical AI',
                'funding_goal': Decimal('6000000.00'),
                'url': 'https://neurovision.health',
            },
            {
                'name': 'GreenEnergy Grid',
                'description': 'Smart grid optimization platform that maximizes renewable energy efficiency and reduces costs.',
                'problem': 'Renewable energy sources are intermittent and expensive to integrate into existing power grids.',
                'market': 'Smart grid market valued at $28B, growing at 15% annually as countries transition to clean energy.',
                'competition': 'Siemens and GE Digital Energy lead, but our AI optimization provides 25% better efficiency.',
                'details': 'Our machine learning algorithms predict energy demand and optimize renewable energy distribution in real-time.',
                'stage': 'Series A',
                'category': 'Clean Energy',
                'funding_goal': Decimal('7000000.00'),
                'url': 'https://greenenergygrid.com',
            },
            {
                'name': 'VirtualReality Pro',
                'description': 'Enterprise VR platform for remote collaboration, training, and immersive business applications.',
                'problem': 'Remote work lacks the personal connection and hands-on training that physical offices provide.',
                'market': 'Enterprise VR market expected to reach $4.3B by 2025, driven by remote work and training needs.',
                'competition': 'Meta Horizon Workrooms and Microsoft Mesh are developing solutions, but we offer better enterprise integration.',
                'details': 'Our platform provides photorealistic avatars and spatial audio for truly immersive remote collaboration.',
                'stage': 'Seed',
                'category': 'VR/AR',
                'funding_goal': Decimal('3000000.00'),
                'url': 'https://vrpro.enterprise',
            },
            {
                'name': 'DataGuardian',
                'description': 'AI-powered data privacy platform that automatically detects and protects sensitive information.',
                'problem': 'Data breaches cost companies $4.45M on average, with 90% caused by human error or misconfigured systems.',
                'market': 'Data privacy software market growing at 20% annually, reaching $2.1B by 2025.',
                'competition': 'OneTrust and TrustArc dominate compliance, but we offer real-time data protection.',
                'details': 'Our AI continuously monitors data flows and automatically applies appropriate privacy controls and encryption.',
                'stage': 'Series A',
                'category': 'Cybersecurity',
                'funding_goal': Decimal('5000000.00'),
                'url': 'https://dataguardian.security',
            },
            {
                'name': 'AgriTech AI',
                'description': 'Precision agriculture platform that uses AI and IoT to optimize crop yields and reduce environmental impact.',
                'problem': 'Global food production must increase 70% by 2050 while reducing water usage and environmental impact.',
                'market': 'Precision agriculture market valued at $7.6B, growing at 12% annually as farmers adopt smart farming.',
                'competition': 'John Deere and Trimble lead, but our AI provides more accurate predictions and recommendations.',
                'details': 'Our platform analyzes satellite imagery, weather data, and soil conditions to optimize every aspect of farming.',
                'stage': 'Series A',
                'category': 'AgTech',
                'funding_goal': Decimal('4000000.00'),
                'url': 'https://agritech-ai.farm',
            },
            {
                'name': 'FinTech Flow',
                'description': 'Real-time payment processing platform that enables instant cross-border transactions with minimal fees.',
                'problem': 'Traditional banking systems are slow, expensive, and exclude billions of people from financial services.',
                'market': 'Global payments market valued at $2.1T, with real-time payments growing at 30% annually.',
                'competition': 'Stripe and PayPal dominate online payments, but we offer better cross-border capabilities.',
                'details': 'Our blockchain-based platform processes payments in seconds with fees under 0.1% globally.',
                'stage': 'Series A',
                'category': 'FinTech',
                'funding_goal': Decimal('6000000.00'),
                'url': 'https://fintechflow.pay',
            },
            {
                'name': 'EduTech Pro',
                'description': 'Personalized learning platform that adapts to each student\'s learning style and pace using AI.',
                'problem': 'Traditional education is one-size-fits-all, leaving many students behind or not challenged enough.',
                'market': 'EdTech market projected to reach $377B by 2028, with personalized learning being the fastest-growing segment.',
                'competition': 'Khan Academy and Coursera are popular, but we offer true personalization for every student.',
                'details': 'Our AI creates custom learning paths and adapts content difficulty in real-time based on student performance.',
                'stage': 'Seed',
                'category': 'EdTech',
                'funding_goal': Decimal('2000000.00'),
                'url': 'https://edutechpro.learn',
            },
            {
                'name': 'LogisticsAI',
                'description': 'Autonomous logistics platform that optimizes supply chain operations using AI and robotics.',
                'problem': 'Supply chain disruptions cost companies $4.6T annually, with manual processes being inefficient and error-prone.',
                'market': 'Supply chain management market valued at $37.4B, with AI adoption growing at 25% annually.',
                'competition': 'SAP and Oracle dominate ERP, but we offer end-to-end autonomous logistics optimization.',
                'details': 'Our AI predicts demand, optimizes routes, and coordinates autonomous vehicles for seamless logistics.',
                'stage': 'Series A',
                'category': 'Logistics',
                'funding_goal': Decimal('8000000.00'),
                'url': 'https://logisticsai.supply',
            },
            {
                'name': 'HealthTech Connect',
                'description': 'Telemedicine platform that connects patients with specialists worldwide using AI-powered diagnostics.',
                'problem': 'Access to quality healthcare is limited by geography, with 3.5B people lacking access to essential health services.',
                'market': 'Telemedicine market expected to reach $185B by 2030, driven by COVID-19 and rural healthcare needs.',
                'competition': 'Teladoc and Amwell lead, but we offer AI-powered preliminary diagnostics and specialist matching.',
                'details': 'Our AI analyzes symptoms and medical history to connect patients with the most appropriate specialists globally.',
                'stage': 'Series A',
                'category': 'HealthTech',
                'funding_goal': Decimal('5000000.00'),
                'url': 'https://healthtechconnect.care',
            },
            {
                'name': 'Proptech AI',
                'description': 'Smart building management platform that optimizes energy usage and tenant experience using IoT and AI.',
                'problem': 'Buildings consume 40% of global energy, with most systems operating inefficiently and lacking automation.',
                'market': 'Smart building market valued at $80B, growing at 12% annually as buildings become more connected.',
                'competition': 'Honeywell and Johnson Controls lead, but our AI provides more intelligent automation and optimization.',
                'details': 'Our platform learns from building usage patterns to optimize HVAC, lighting, and security systems automatically.',
                'stage': 'Seed',
                'category': 'PropTech',
                'funding_goal': Decimal('3000000.00'),
                'url': 'https://proptech-ai.build',
            },
            {
                'name': 'RetailAI',
                'description': 'AI-powered retail optimization platform that personalizes customer experience and optimizes inventory.',
                'problem': 'Retailers struggle with inventory management, customer personalization, and predicting demand accurately.',
                'market': 'Retail AI market projected to reach $19.9B by 2027, with personalization being the key growth driver.',
                'competition': 'Amazon and Shopify dominate e-commerce, but we offer better personalization for physical stores.',
                'details': 'Our AI analyzes customer behavior, weather, and trends to optimize inventory and create personalized shopping experiences.',
                'stage': 'Series A',
                'category': 'Retail Tech',
                'funding_goal': Decimal('4000000.00'),
                'url': 'https://retailai.shop',
            },
            {
                'name': 'TransportAI',
                'description': 'Autonomous vehicle fleet management platform for ride-sharing and delivery services.',
                'problem': 'Urban transportation is inefficient, expensive, and contributes to traffic congestion and pollution.',
                'market': 'Autonomous vehicle market expected to reach $556B by 2026, with fleet management being crucial for adoption.',
                'competition': 'Waymo and Cruise lead AV development, but we focus on fleet optimization and business models.',
                'details': 'Our platform manages autonomous vehicle fleets, optimizing routes and pricing for maximum efficiency and profitability.',
                'stage': 'Series A',
                'category': 'Transportation',
                'funding_goal': Decimal('10000000.00'),
                'url': 'https://transportai.mobility',
            },
            {
                'name': 'MediaAI',
                'description': 'AI-powered content creation platform that generates personalized videos, articles, and social media content.',
                'problem': 'Content creation is time-consuming and expensive, with most content failing to engage target audiences effectively.',
                'market': 'Content marketing market valued at $42B, with AI-generated content growing at 30% annually.',
                'competition': 'Jasper and Copy.ai lead AI writing, but we offer full multimedia content creation and personalization.',
                'details': 'Our AI creates personalized content across all media formats, analyzing audience preferences for maximum engagement.',
                'stage': 'Seed',
                'category': 'Media Tech',
                'funding_goal': Decimal('2500000.00'),
                'url': 'https://mediaai.create',
            },
            {
                'name': 'GamingAI',
                'description': 'AI-powered game development platform that creates procedurally generated content and intelligent NPCs.',
                'problem': 'Game development is expensive and time-consuming, with content creation being the biggest bottleneck.',
                'market': 'Game development market valued at $180B, with procedural generation and AI becoming standard features.',
                'competition': 'Unity and Unreal Engine dominate development, but we offer AI-powered content generation and NPCs.',
                'details': 'Our AI generates infinite game content, creates intelligent NPCs, and adapts gameplay to individual player preferences.',
                'stage': 'Series A',
                'category': 'Gaming',
                'funding_goal': Decimal('5000000.00'),
                'url': 'https://gamingai.dev',
            },
            {
                'name': 'SocialAI',
                'description': 'AI-powered social media platform that connects people based on interests and values rather than algorithms.',
                'problem': 'Current social media platforms prioritize engagement over meaningful connections, leading to echo chambers and misinformation.',
                'market': 'Social media market valued at $192B, with users increasingly seeking authentic connections and positive experiences.',
                'competition': 'Meta and TikTok dominate, but we focus on meaningful connections and positive social impact.',
                'details': 'Our AI matches users based on shared values and interests, creating meaningful communities and reducing toxic content.',
                'stage': 'Seed',
                'category': 'Social Media',
                'funding_goal': Decimal('3000000.00'),
                'url': 'https://socialai.connect',
            },
            {
                'name': 'TravelAI',
                'description': 'AI-powered travel planning platform that creates personalized itineraries and handles all booking automatically.',
                'problem': 'Travel planning is overwhelming and time-consuming, with most people missing out on unique experiences.',
                'market': 'Online travel market valued at $432B, with personalization being the key differentiator for success.',
                'competition': 'Booking.com and Expedia dominate, but we offer true personalization and unique experience discovery.',
                'details': 'Our AI learns from your preferences and creates custom travel experiences, handling all bookings and logistics automatically.',
                'stage': 'Series A',
                'category': 'Travel Tech',
                'funding_goal': Decimal('4000000.00'),
                'url': 'https://travelai.explore',
            },
            {
                'name': 'FitnessAI',
                'description': 'AI-powered fitness platform that creates personalized workout plans and provides real-time coaching.',
                'problem': 'Most people struggle to maintain consistent fitness routines due to lack of personalization and motivation.',
                'market': 'Fitness app market valued at $4.4B, with AI-powered personalization being the fastest-growing segment.',
                'competition': 'Peloton and MyFitnessPal are popular, but we offer true AI personalization and real-time form correction.',
                'details': 'Our AI analyzes your movement patterns, fitness goals, and preferences to create optimal workout plans with real-time coaching.',
                'stage': 'Seed',
                'category': 'Fitness Tech',
                'funding_goal': Decimal('2000000.00'),
                'url': 'https://fitnessai.train',
            }
        ]

        created_count = 0
        for startup_data in yc_startups:
            # Check if project already exists
            if not Project.objects.filter(name=startup_data['name']).exists():
                # Add some random funding to make it realistic
                current_funding = Decimal(str(random.uniform(0.1, 0.8))) * startup_data['funding_goal']
                
                # Set banner image path
                banner_filename = f"banners/{startup_data['name'].replace(' ', '_').replace('-', '_').lower()}.png"
                banner_path = os.path.join('media', banner_filename)
                
                project = Project.objects.create(
                    user=system_user,
                    name=startup_data['name'],
                    description=startup_data['description'],
                    problem=startup_data['problem'],
                    market=startup_data['market'],
                    competition=startup_data['competition'],
                    details=startup_data['details'],
                    stage=startup_data['stage'],
                    category=startup_data['category'],
                    url=startup_data['url'],
                    funding_goal=startup_data['funding_goal'],
                    created_at=timezone.now()
                )
                
                # Set banner if file exists
                if os.path.exists(banner_path):
                    project.banner = banner_filename
                    project.save()
                
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created startup: {startup_data["name"]}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Startup already exists: {startup_data["name"]}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} Y Combinator Fall 2025 startups!')
        )
