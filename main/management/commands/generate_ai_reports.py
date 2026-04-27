"""
Django management command to generate AI analyst reports for all projects.
"""

from django.core.management.base import BaseCommand
from main.models import Project, AIAnalystReport
from main.ai_analyst import ai_analyst
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate AI analyst reports for all projects'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project-id',
            type=int,
            help='Generate report for specific project only',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regenerate all reports',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🤖 Starting AI analyst report generation...'))
        
        # Check current data
        total_projects = Project.objects.count()
        total_reports = AIAnalystReport.objects.count()
        
        self.stdout.write(f"📊 Current data:")
        self.stdout.write(f"   Projects: {total_projects}")
        self.stdout.write(f"   Existing Reports: {total_reports}")
        
        if options['project_id']:
            try:
                project = Project.objects.get(id=options['project_id'])
                self.generate_project_report(project, force=options['force'])
            except Project.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Project with ID {options["project_id"]} not found'))
        else:
            self.generate_all_reports(force=options['force'])
    
    def generate_project_report(self, project, force=False):
        """Generate AI report for a specific project"""
        self.stdout.write(f"🤖 Generating AI report for: {project.name}")
        
        if force and AIAnalystReport.objects.filter(project=project).exists():
            AIAnalystReport.objects.filter(project=project).delete()
            self.stdout.write(f"   Deleted existing report for {project.name}")
        
        try:
            report = ai_analyst.generate_report(project)
            self.stdout.write(self.style.SUCCESS(f"✅ Generated AI report for {project.name}"))
            self.stdout.write(f"   Risk Level: {report.risk_level} ({report.risk_score}/100)")
            self.stdout.write(f"   Growth Index: {report.growth_index} ({report.growth_score}/100)")
            self.stdout.write(f"   Sector Rank: #{report.sector_rank}")
            self.stdout.write(f"   Platform Rank: #{report.platform_rank}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error generating report for {project.name}: {str(e)}"))
    
    def generate_all_reports(self, force=False):
        """Generate AI reports for all projects"""
        self.stdout.write('🤖 Generating AI reports for all projects...')
        
        projects = Project.objects.all()
        success_count = 0
        
        for project in projects:
            try:
                self.generate_project_report(project, force=force)
                success_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error for {project.name}: {str(e)}"))
        
        self.stdout.write(self.style.SUCCESS(f'🎉 Generated AI reports for {success_count}/{projects.count()} projects'))
