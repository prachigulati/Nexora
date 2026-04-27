from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import models
from main.models import Project, Position, Transaction
from django.utils import timezone
from decimal import Decimal
import random
import os
from PIL import Image, ImageDraw, ImageFont

class Command(BaseCommand):
    help = 'Update all Y Combinator startups with positions, ETH funding, and unique logos'

    def create_unique_logo(self, name, category, index):
        """Create a unique logo for each startup based on name and index"""
        width, height = 400, 200
        
        # Generate unique colors based on name hash
        name_hash = hash(name) % 1000
        color_variations = [
            {'bg': (30, 50, 80), 'accent': (100, 200, 255), 'text': (255, 255, 255)},
            {'bg': (20, 20, 40), 'accent': (150, 100, 255), 'text': (255, 255, 255)},
            {'bg': (20, 60, 40), 'accent': (100, 255, 150), 'text': (255, 255, 255)},
            {'bg': (40, 20, 60), 'accent': (200, 100, 255), 'text': (255, 255, 255)},
            {'bg': (60, 30, 50), 'accent': (255, 150, 200), 'text': (255, 255, 255)},
            {'bg': (50, 50, 30), 'accent': (255, 255, 150), 'text': (255, 255, 255)},
            {'bg': (30, 40, 20), 'accent': (200, 255, 100), 'text': (255, 255, 255)},
            {'bg': (80, 40, 20), 'accent': (255, 200, 100), 'text': (255, 255, 255)},
            {'bg': (60, 20, 40), 'accent': (255, 100, 150), 'text': (255, 255, 255)},
            {'bg': (20, 50, 30), 'accent': (100, 255, 150), 'text': (255, 255, 255)},
        ]
        
        logo_style = color_variations[index % len(color_variations)]
        
        # Create image with unique background
        img = Image.new('RGB', (width, height), logo_style['bg'])
        draw = ImageDraw.Draw(img)
        
        # Create unique pattern based on startup name and index
        pattern_type = (name_hash + index) % 6
        
        if pattern_type == 0:
            # Circular pattern
            for i in range(6):
                radius = 15 + i * 12
                alpha = 40 + i * 15
                draw.ellipse([width//2-radius, height//2-radius, width//2+radius, height//2+radius], 
                           outline=(*logo_style['accent'], alpha), width=2)
        elif pattern_type == 1:
            # Triangular pattern
            for i in range(5):
                size = 25 + i * 15
                points = [(width//2, height//2-size), 
                         (width//2-size, height//2+size), 
                         (width//2+size, height//2+size)]
                draw.polygon(points, outline=logo_style['accent'], width=2)
        elif pattern_type == 2:
            # Hexagonal pattern
            for i in range(4):
                size = 20 + i * 12
                hex_points = []
                for j in range(6):
                    angle = j * 60
                    x = width//2 + size * (0.866 * (1 if angle < 180 else -1) if angle % 120 != 0 else 0)
                    y = height//2 + size * (0.5 if angle < 60 or angle > 300 else -0.5 if angle < 180 else 0)
                    hex_points.append((x, y))
                draw.polygon(hex_points, outline=logo_style['accent'], width=2)
        elif pattern_type == 3:
            # Square pattern
            for i in range(5):
                size = 15 + i * 12
                draw.rectangle([width//2-size, height//2-size, width//2+size, height//2+size], 
                             outline=logo_style['accent'], width=2)
        elif pattern_type == 4:
            # Wave pattern
            for i in range(3):
                y_offset = 30 + i * 50
                for x in range(0, width, 10):
                    y = y_offset + 10 * (1 if (x // 20) % 2 == 0 else -1)
                    draw.point((x, y), fill=logo_style['accent'])
        else:
            # Grid pattern
            for i in range(8):
                x = 30 + (i % 4) * 90
                y = 30 + (i // 4) * 140
                draw.rectangle([x-8, y-8, x+8, y+8], outline=logo_style['accent'], width=2)
        
        # Add company name with unique styling
        try:
            font_large = ImageFont.truetype("arial.ttf", 18)
            font_small = ImageFont.truetype("arial.ttf", 10)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Draw company name with unique positioning
        text_bbox = draw.textbbox((0, 0), name, font=font_large)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (width - text_width) // 2
        text_y = height // 2 - 12
        
        # Add text shadow
        draw.text((text_x+1, text_y+1), name, fill=(0, 0, 0, 100), font=font_large)
        draw.text((text_x, text_y), name, fill=logo_style['text'], font=font_large)
        
        # Draw category with unique styling
        category_bbox = draw.textbbox((0, 0), category, font=font_small)
        category_width = category_bbox[2] - category_bbox[0]
        category_x = (width - category_width) // 2
        category_y = text_y + 20
        
        draw.text((category_x, category_y), category, fill=logo_style['text'], font=font_small)
        
        # Add unique decorative elements
        decoration_type = (name_hash + index * 2) % 4
        if decoration_type == 0:
            # Dots pattern
            for i in range(12):
                x = 20 + (i % 6) * 60
                y = 20 + (i // 6) * 160
                draw.ellipse([x-2, y-2, x+2, y+2], fill=logo_style['accent'])
        elif decoration_type == 1:
            # Lines pattern
            for i in range(8):
                x1 = 15 + i * 45
                y1 = 15 + (i % 2) * 170
                x2 = x1 + 30
                y2 = y1 + 15
                draw.line([(x1, y1), (x2, y2)], fill=logo_style['accent'], width=1)
        elif decoration_type == 2:
            # Arcs pattern
            for i in range(6):
                x = 30 + i * 60
                y = 30 + (i % 2) * 140
                draw.arc([x-15, y-15, x+15, y+15], 0, 180, fill=logo_style['accent'], width=1)
        else:
            # Cross pattern
            for i in range(6):
                x = 25 + i * 60
                y = 25 + (i % 2) * 150
                draw.line([(x-8, y), (x+8, y)], fill=logo_style['accent'], width=1)
                draw.line([(x, y-8), (x, y+8)], fill=logo_style['accent'], width=1)
        
        return img

    def handle(self, *args, **options):
        # Get system user
        system_user = User.objects.get(username='yc_system')
        
        # All startup data with realistic ETH funding goals and positions
        all_startups = [
            {
                'name': 'NeuralLink AI',
                'category': 'Healthcare AI',
                'funding_goal_eth': Decimal('1000.0'),
                'current_funding_eth': Decimal('650.0'),
                'positions': [
                    {'title': 'Senior ML Engineer', 'description': 'Lead development of neural signal processing algorithms using deep learning and signal processing techniques.', 'compensation': 'paid'},
                    {'title': 'Neuroscience Researcher', 'description': 'Research and develop non-invasive neural interface technologies for medical applications.', 'compensation': 'paid'},
                    {'title': 'Product Manager', 'description': 'Define product roadmap and work with engineering team to deliver medical-grade neural interface solutions.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'QuantumFlow',
                'category': 'Quantum Computing',
                'funding_goal_eth': Decimal('600.0'),
                'current_funding_eth': Decimal('180.0'),
                'positions': [
                    {'title': 'Quantum Software Engineer', 'description': 'Develop quantum algorithms and software tools for enterprise quantum computing applications.', 'compensation': 'paid'},
                    {'title': 'Quantum Hardware Engineer', 'description': 'Design and optimize quantum computing hardware and control systems.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'CarbonCapture Pro',
                'category': 'Climate Tech',
                'funding_goal_eth': Decimal('2000.0'),
                'current_funding_eth': Decimal('1200.0'),
                'positions': [
                    {'title': 'Chemical Engineer', 'description': 'Design and optimize carbon capture processes and membrane technologies.', 'compensation': 'paid'},
                    {'title': 'Climate Scientist', 'description': 'Research atmospheric CO2 dynamics and develop carbon utilization strategies.', 'compensation': 'paid'},
                    {'title': 'Business Development', 'description': 'Build partnerships with corporations and governments for carbon capture solutions.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'SpaceLogistics',
                'category': 'Space Tech',
                'funding_goal_eth': Decimal('1200.0'),
                'current_funding_eth': Decimal('360.0'),
                'positions': [
                    {'title': 'Aerospace Engineer', 'description': 'Design autonomous spacecraft systems for debris capture and satellite servicing.', 'compensation': 'paid'},
                    {'title': 'Robotics Engineer', 'description': 'Develop robotic systems for space debris capture and manipulation.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'BioPrint Solutions',
                'category': 'Biotech',
                'funding_goal_eth': Decimal('3200.0'),
                'current_funding_eth': Decimal('2240.0'),
                'positions': [
                    {'title': 'Bioengineer', 'description': 'Develop bioinks and 3D printing processes for organ and tissue fabrication.', 'compensation': 'paid'},
                    {'title': 'Cell Biologist', 'description': 'Research cell behavior and develop protocols for maintaining cell viability in printed tissues.', 'compensation': 'paid'},
                    {'title': 'Regulatory Affairs', 'description': 'Navigate FDA approval process for bioprinted organs and medical devices.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'EdgeCompute AI',
                'category': 'Edge Computing',
                'funding_goal_eth': Decimal('800.0'),
                'current_funding_eth': Decimal('240.0'),
                'positions': [
                    {'title': 'Edge AI Engineer', 'description': 'Develop AI models optimized for edge devices with minimal power consumption.', 'compensation': 'paid'},
                    {'title': 'Hardware Engineer', 'description': 'Design and optimize hardware acceleration for AI inference on edge devices.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'CryptoVault',
                'category': 'Blockchain',
                'funding_goal_eth': Decimal('1600.0'),
                'current_funding_eth': Decimal('800.0'),
                'positions': [
                    {'title': 'Blockchain Developer', 'description': 'Develop quantum-resistant cryptographic protocols and secure wallet infrastructure.', 'compensation': 'paid'},
                    {'title': 'Security Engineer', 'description': 'Implement military-grade security measures for cryptocurrency storage and transactions.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'RoboChef',
                'category': 'Food Tech',
                'funding_goal_eth': Decimal('1000.0'),
                'current_funding_eth': Decimal('300.0'),
                'positions': [
                    {'title': 'Robotics Engineer', 'description': 'Design and develop autonomous robotic systems for food preparation and cooking.', 'compensation': 'paid'},
                    {'title': 'AI Engineer', 'description': 'Develop computer vision and machine learning algorithms for food recognition and cooking processes.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'NeuroVision',
                'category': 'Medical AI',
                'funding_goal_eth': Decimal('2400.0'),
                'current_funding_eth': Decimal('1440.0'),
                'positions': [
                    {'title': 'Medical AI Engineer', 'description': 'Develop deep learning models for medical image analysis and disease detection.', 'compensation': 'paid'},
                    {'title': 'Radiologist Consultant', 'description': 'Provide medical expertise for AI model training and validation in diagnostic imaging.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'GreenEnergy Grid',
                'category': 'Clean Energy',
                'funding_goal_eth': Decimal('2800.0'),
                'current_funding_eth': Decimal('1680.0'),
                'positions': [
                    {'title': 'Energy Systems Engineer', 'description': 'Design and optimize smart grid systems for renewable energy integration.', 'compensation': 'paid'},
                    {'title': 'AI Optimization Engineer', 'description': 'Develop machine learning algorithms for energy demand prediction and grid optimization.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'VirtualReality Pro',
                'category': 'VR/AR',
                'funding_goal_eth': Decimal('1200.0'),
                'current_funding_eth': Decimal('360.0'),
                'positions': [
                    {'title': 'VR Developer', 'description': 'Develop immersive VR applications and experiences for enterprise collaboration.', 'compensation': 'paid'},
                    {'title': '3D Graphics Engineer', 'description': 'Create photorealistic avatars and environments for virtual meetings and training.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'DataGuardian',
                'category': 'Cybersecurity',
                'funding_goal_eth': Decimal('2000.0'),
                'current_funding_eth': Decimal('1000.0'),
                'positions': [
                    {'title': 'Security Engineer', 'description': 'Develop AI-powered data protection and privacy monitoring systems.', 'compensation': 'paid'},
                    {'title': 'Privacy Compliance Specialist', 'description': 'Ensure compliance with data protection regulations and implement privacy controls.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'AgriTech AI',
                'category': 'AgTech',
                'funding_goal_eth': Decimal('1600.0'),
                'current_funding_eth': Decimal('800.0'),
                'positions': [
                    {'title': 'Agricultural AI Engineer', 'description': 'Develop AI models for crop monitoring, yield prediction, and precision agriculture.', 'compensation': 'paid'},
                    {'title': 'IoT Engineer', 'description': 'Design and implement sensor networks for farm monitoring and data collection.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'FinTech Flow',
                'category': 'FinTech',
                'funding_goal_eth': Decimal('2400.0'),
                'current_funding_eth': Decimal('1200.0'),
                'positions': [
                    {'title': 'Blockchain Developer', 'description': 'Develop real-time payment processing systems using blockchain technology.', 'compensation': 'paid'},
                    {'title': 'Financial Systems Engineer', 'description': 'Build secure and scalable payment infrastructure for cross-border transactions.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'EduTech Pro',
                'category': 'EdTech',
                'funding_goal_eth': Decimal('800.0'),
                'current_funding_eth': Decimal('240.0'),
                'positions': [
                    {'title': 'AI Learning Engineer', 'description': 'Develop personalized learning algorithms that adapt to individual student needs.', 'compensation': 'paid'},
                    {'title': 'Educational Content Designer', 'description': 'Create engaging and effective educational content for AI-powered learning platforms.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'LogisticsAI',
                'category': 'Logistics',
                'funding_goal_eth': Decimal('3200.0'),
                'current_funding_eth': Decimal('1920.0'),
                'positions': [
                    {'title': 'Supply Chain AI Engineer', 'description': 'Develop AI algorithms for supply chain optimization and demand forecasting.', 'compensation': 'paid'},
                    {'title': 'Autonomous Systems Engineer', 'description': 'Design and implement autonomous vehicles and robotics for logistics operations.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'HealthTech Connect',
                'category': 'HealthTech',
                'funding_goal_eth': Decimal('2000.0'),
                'current_funding_eth': Decimal('1000.0'),
                'positions': [
                    {'title': 'Telemedicine Platform Engineer', 'description': 'Develop AI-powered telemedicine platform with diagnostic capabilities.', 'compensation': 'paid'},
                    {'title': 'Medical AI Specialist', 'description': 'Implement AI algorithms for symptom analysis and specialist matching.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'Proptech AI',
                'category': 'PropTech',
                'funding_goal_eth': Decimal('1200.0'),
                'current_funding_eth': Decimal('360.0'),
                'positions': [
                    {'title': 'Smart Building Engineer', 'description': 'Develop IoT and AI systems for smart building management and optimization.', 'compensation': 'paid'},
                    {'title': 'Energy Efficiency Specialist', 'description': 'Design and implement energy optimization solutions for commercial buildings.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'RetailAI',
                'category': 'Retail Tech',
                'funding_goal_eth': Decimal('1600.0'),
                'current_funding_eth': Decimal('800.0'),
                'positions': [
                    {'title': 'Retail AI Engineer', 'description': 'Develop AI solutions for inventory management and customer personalization.', 'compensation': 'paid'},
                    {'title': 'Computer Vision Engineer', 'description': 'Implement computer vision systems for retail analytics and customer behavior analysis.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'TransportAI',
                'category': 'Transportation',
                'funding_goal_eth': Decimal('4000.0'),
                'current_funding_eth': Decimal('2000.0'),
                'positions': [
                    {'title': 'Autonomous Vehicle Engineer', 'description': 'Develop autonomous vehicle systems and fleet management algorithms.', 'compensation': 'paid'},
                    {'title': 'Transportation AI Specialist', 'description': 'Create AI models for route optimization and traffic management.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'MediaAI',
                'category': 'Media Tech',
                'funding_goal_eth': Decimal('1000.0'),
                'current_funding_eth': Decimal('300.0'),
                'positions': [
                    {'title': 'AI Content Creator', 'description': 'Develop AI systems for automated content generation across multiple media formats.', 'compensation': 'paid'},
                    {'title': 'Media Platform Engineer', 'description': 'Build scalable platforms for AI-powered content creation and distribution.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'GamingAI',
                'category': 'Gaming',
                'funding_goal_eth': Decimal('2000.0'),
                'current_funding_eth': Decimal('1000.0'),
                'positions': [
                    {'title': 'Game AI Developer', 'description': 'Develop AI systems for procedural content generation and intelligent NPCs.', 'compensation': 'paid'},
                    {'title': 'Game Engine Engineer', 'description': 'Build AI-powered game development tools and platforms.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'SocialAI',
                'category': 'Social Media',
                'funding_goal_eth': Decimal('1200.0'),
                'current_funding_eth': Decimal('360.0'),
                'positions': [
                    {'title': 'Social AI Engineer', 'description': 'Develop AI algorithms for meaningful social connections and content moderation.', 'compensation': 'paid'},
                    {'title': 'Community Platform Developer', 'description': 'Build AI-powered social platforms that foster positive interactions.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'TravelAI',
                'category': 'Travel Tech',
                'funding_goal_eth': Decimal('1600.0'),
                'current_funding_eth': Decimal('800.0'),
                'positions': [
                    {'title': 'Travel AI Engineer', 'description': 'Develop AI systems for personalized travel planning and experience discovery.', 'compensation': 'paid'},
                    {'title': 'Travel Platform Developer', 'description': 'Build comprehensive travel platforms with automated booking and logistics.', 'compensation': 'paid'},
                ]
            },
            {
                'name': 'FitnessAI',
                'category': 'Fitness Tech',
                'funding_goal_eth': Decimal('800.0'),
                'current_funding_eth': Decimal('240.0'),
                'positions': [
                    {'title': 'Fitness AI Engineer', 'description': 'Develop AI systems for personalized workout planning and real-time coaching.', 'compensation': 'paid'},
                    {'title': 'Computer Vision Engineer', 'description': 'Implement computer vision for form analysis and movement tracking.', 'compensation': 'paid'},
                ]
            }
        ]

        updated_count = 0
        created_positions = 0

        for index, startup_info in enumerate(all_startups):
            try:
                # Get project
                project = Project.objects.get(name=startup_info['name'])
                
                # Update funding goal to ETH
                project.funding_goal = startup_info['funding_goal_eth']
                project.save()

                # Add current funding through transactions
                if startup_info['current_funding_eth'] > 0:
                    # Check if funding already exists
                    existing_funding = Transaction.objects.filter(project=project).aggregate(
                        total=models.Sum('amount_eth')
                    )['total'] or Decimal('0')
                    
                    if existing_funding < startup_info['current_funding_eth']:
                        # Add the difference as a transaction
                        additional_funding = startup_info['current_funding_eth'] - existing_funding
                        Transaction.objects.create(
                            user=system_user,
                            user_address='0x0000000000000000000000000000000000000000',  # System address
                            tx_hash=f'system_{project.id}_{timezone.now().timestamp()}_{index}',
                            amount_eth=additional_funding,
                            project=project
                        )

                # Create unique logo
                logo = self.create_unique_logo(startup_info['name'], startup_info['category'], index)
                
                # Save logo
                logo_filename = f"banners/{startup_info['name'].replace(' ', '_').replace('-', '_').lower()}.png"
                logo_path = os.path.join('media', logo_filename)
                os.makedirs(os.path.dirname(logo_path), exist_ok=True)
                logo.save(logo_path)
                
                # Update project with logo
                project.banner = logo_filename
                project.save()

                # Add positions
                for position_data in startup_info['positions']:
                    position, pos_created = Position.objects.get_or_create(
                        project=project,
                        title=position_data['title'],
                        defaults={
                            'description': position_data['description'],
                            'compensation_type': position_data['compensation']
                        }
                    )
                    if pos_created:
                        created_positions += 1

                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Updated {startup_info["name"]} - {startup_info["current_funding_eth"]} ETH / {startup_info["funding_goal_eth"]} ETH ({len(startup_info["positions"])} positions)')
                )

            except Project.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Project not found: {startup_info["name"]}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error updating {startup_info["name"]}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} startups with {created_positions} new positions!')
        )
