"""
Management command to generate AI analysis for all projects that don't have it.
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from main.models import Project, AIAnalystReport
from main.ai_analyst import ai_analyst
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate AI analysis for all projects that don\'t have it'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration of existing AI analysis',
        )
        parser.add_argument(
            '--project-id',
            type=int,
            help='Generate analysis for a specific project ID only',
        )

    def handle(self, *args, **options):
        force = options['force']
        project_id = options.get('project_id')
        
        if project_id:
            # Generate for specific project
            try:
                project = Project.objects.get(id=project_id)
                self.generate_analysis_for_project(project, force)
            except Project.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Project with ID {project_id} not found')
                )
        else:
            # Generate for all projects
            if force:
                projects = Project.objects.all()
                self.stdout.write(
                    self.style.WARNING('Force mode: Regenerating all AI analysis')
                )
            else:
                # Only projects without AI analysis
                projects = Project.objects.filter(
                    ~Q(ai_report__isnull=False)
                )
            
            total_projects = projects.count()
            self.stdout.write(f'Found {total_projects} projects to process')
            
            if total_projects == 0:
                self.stdout.write(
                    self.style.SUCCESS('All projects already have AI analysis!')
                )
                return
            
            success_count = 0
            error_count = 0
            
            for i, project in enumerate(projects, 1):
                self.stdout.write(f'Processing project {i}/{total_projects}: {project.name}')
                
                try:
                    self.generate_analysis_for_project(project, force)
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Generated analysis for: {project.name}')
                    )
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'Error for {project.name}: {str(e)}')
                    )
                    logger.error(f"Error generating AI analysis for {project.name}: {str(e)}")
            
            # Summary
            self.stdout.write('\n' + '='*50)
            self.stdout.write(f'Summary:')
            self.stdout.write(f'  Success: {success_count}')
            self.stdout.write(f'  Errors: {error_count}')
            self.stdout.write(f'  Total: {total_projects}')
            
            if error_count == 0:
                self.stdout.write(
                    self.style.SUCCESS('\nAll AI analysis generated successfully!')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'\n{error_count} projects failed. Check logs for details.')
                )

    def generate_analysis_for_project(self, project, force=False):
        """Generate AI analysis for a single project"""
        try:
            # Check if analysis already exists
            if not force and AIAnalystReport.objects.filter(project=project).exists():
                self.stdout.write(
                    self.style.WARNING(f'  AI analysis already exists for: {project.name}')
                )
                return
            
            # Delete existing analysis if force mode
            if force:
                AIAnalystReport.objects.filter(project=project).delete()
            
            # Generate new analysis
            self.stdout.write(f'  Generating AI analysis...')
            report = ai_analyst.generate_report(project)
            
            self.stdout.write(
                f'  Risk: {report.risk_level} ({report.risk_score}/100)'
            )
            self.stdout.write(
                f'  Growth: {report.growth_index} ({report.growth_score}/100)'
            )
            
        except Exception as e:
            logger.error(f"Error generating AI analysis for {project.name}: {str(e)}")
            raise e
