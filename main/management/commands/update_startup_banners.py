from django.core.management.base import BaseCommand
from main.models import Project
import os

class Command(BaseCommand):
    help = 'Update existing startups with banner images'

    def handle(self, *args, **options):
        updated_count = 0
        
        # Get all projects
        projects = Project.objects.all()
        
        for project in projects:
            # Generate banner filename
            banner_filename = f"banners/{project.name.replace(' ', '_').replace('-', '_').lower()}.png"
            banner_path = os.path.join('media', banner_filename)
            
            # Check if banner file exists and project doesn't have a banner
            if os.path.exists(banner_path) and not project.banner:
                project.banner = banner_filename
                project.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Updated banner for: {project.name}')
                )
            elif not os.path.exists(banner_path):
                self.stdout.write(
                    self.style.WARNING(f'Banner not found for: {project.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Banner already exists for: {project.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} startup banners!')
        )
