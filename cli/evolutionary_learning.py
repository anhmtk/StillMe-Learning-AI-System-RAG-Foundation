#!/usr/bin/env python3
"""
🧠 StillMe Evolutionary Learning CLI
===================================

CLI tool để quản lý hệ thống học tập tiến hóa của StillMe.
Hỗ trợ daily training, self-assessment, và evolution management.

Usage:
    python -m cli.evolutionary_learning status
    python -m cli.evolutionary_learning train --session-type daily
    python -m cli.evolutionary_learning assess --type full
    python -m cli.evolutionary_learning evolve --force
    python -m cli.evolutionary_learning reset --confirm

Author: StillMe AI Framework
Version: 2.0.0
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from stillme_core.learning.evolutionary_learning_system import (
    EvolutionaryLearningSystem,
    EvolutionaryConfig,
    EvolutionStage,
    LearningMode,
    get_evolutionary_learning_system
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EvolutionaryLearningCLI:
    """CLI for Evolutionary Learning System"""
    
    def __init__(self):
        self.system = get_evolutionary_learning_system()
    
    async def status(self, args):
        """Show learning system status"""
        print("🧠 StillMe Evolutionary Learning System Status")
        print("=" * 50)
        
        status = self.system.get_learning_status()
        
        print(f"Current Stage: {status['current_stage'].upper()}")
        print(f"Evolution Progress: {status['evolution_progress']:.1%}")
        print(f"System Age: {status['system_age_days']} days")
        print(f"Overall Score: {status['overall_score']:.2f}")
        print()
        
        print("📊 Learning Metrics:")
        metrics = status['learning_metrics']
        print(f"  Accuracy: {metrics['accuracy']:.2f}")
        print(f"  Response Time: {metrics['response_time']:.2f}s")
        print(f"  User Satisfaction: {metrics['user_satisfaction']:.2f}")
        print(f"  Knowledge Retention: {metrics['knowledge_retention']:.2f}")
        print(f"  Adaptation Speed: {metrics['adaptation_speed']:.2f}")
        print(f"  Creativity Score: {metrics['creativity_score']:.2f}")
        print(f"  Consistency Score: {metrics['consistency_score']:.2f}")
        print()
        
        print("📈 Recent Activity:")
        print(f"  Training Sessions: {status['recent_sessions']}")
        print(f"  Knowledge Gaps: {status['knowledge_gaps']}")
        print(f"  Improvement Areas: {status['improvement_areas']}")
        print()
        
        # Show evolution path
        print("🔄 Evolution Path:")
        stages = [EvolutionStage.INFANT, EvolutionStage.CHILD, 
                 EvolutionStage.ADOLESCENT, EvolutionStage.ADULT]
        current_stage = EvolutionStage(status['current_stage'])
        
        for i, stage in enumerate(stages):
            if stage == current_stage:
                print(f"  {i+1}. {stage.value.upper()} ← CURRENT")
            elif stages.index(stage) < stages.index(current_stage):
                print(f"  {i+1}. {stage.value.upper()} ✓ COMPLETED")
            else:
                print(f"  {i+1}. {stage.value.upper()}")
    
    async def train(self, args):
        """Run training session"""
        session_type = args.session_type or 'daily'
        
        print(f"🏋️ Starting {session_type} training session...")
        print("=" * 40)
        
        try:
            if session_type == 'daily':
                session = await self.system.daily_learning_session()
            else:
                # Custom training session
                session = await self._custom_training_session(args)
            
            print(f"✅ Training session completed: {session.session_id}")
            print(f"Duration: {session.duration_minutes} minutes")
            print(f"Exercises completed: {session.exercises_completed}")
            print(f"Accuracy improvement: {session.accuracy_improvement:.2%}")
            print(f"New patterns learned: {session.new_patterns_learned}")
            print(f"Knowledge gaps identified: {len(session.knowledge_gaps_identified)}")
            
            if session.knowledge_gaps_identified:
                print("\n🎯 Knowledge Gaps:")
                for gap in session.knowledge_gaps_identified:
                    print(f"  - {gap}")
            
            print("\n📋 Next Session Plan:")
            for key, value in session.next_session_plan.items():
                print(f"  {key}: {value}")
                
        except Exception as e:
            logger.error(f"Training session failed: {e}")
            print(f"❌ Training session failed: {e}")
    
    async def assess(self, args):
        """Run self-assessment"""
        assessment_type = args.type or 'full'
        
        print(f"🔍 Running {assessment_type} self-assessment...")
        print("=" * 40)
        
        try:
            assessment = await self.system._perform_self_assessment()
            
            print(f"Overall Score: {assessment['overall_score']:.2f}")
            print(f"Evolution Progress: {assessment['evolution_progress']:.1%}")
            print()
            
            if assessment['knowledge_gaps']:
                print("🎯 Knowledge Gaps:")
                for gap in assessment['knowledge_gaps']:
                    print(f"  - {gap}")
                print()
            
            if assessment['performance_weaknesses']:
                print("⚠️ Performance Weaknesses:")
                for weakness in assessment['performance_weaknesses']:
                    print(f"  - {weakness}")
                print()
            
            if assessment['improvement_areas']:
                print("📈 Improvement Areas:")
                for area in assessment['improvement_areas']:
                    print(f"  - {area}")
                print()
            
            # Recommendations
            print("💡 Recommendations:")
            if assessment['overall_score'] < 0.7:
                print("  - Increase daily training duration")
                print("  - Focus on knowledge gap exercises")
            if assessment['evolution_progress'] < 0.5:
                print("  - Review and learn from more experiences")
                print("  - Practice consistency exercises")
            
        except Exception as e:
            logger.error(f"Self-assessment failed: {e}")
            print(f"❌ Self-assessment failed: {e}")
    
    async def evolve(self, args):
        """Trigger evolution to next stage"""
        force = args.force
        
        print("🔄 Checking evolution readiness...")
        print("=" * 40)
        
        current_stage = self.system.current_stage
        progress = self.system._calculate_evolution_progress()
        
        print(f"Current Stage: {current_stage.value.upper()}")
        print(f"Evolution Progress: {progress:.1%}")
        
        if current_stage == EvolutionStage.ADULT:
            print("🎉 Already at maximum evolution stage!")
            return
        
        if progress >= 0.8 or force:
            print("✅ Ready for evolution!")
            
            if not force:
                confirm = input("Proceed with evolution? (y/N): ")
                if confirm.lower() != 'y':
                    print("Evolution cancelled.")
                    return
            
            success = await self.system.evolve_to_next_stage()
            
            if success:
                new_stage = self.system.current_stage
                print(f"🎉 Successfully evolved to {new_stage.value.upper()}!")
                print(f"New configuration applied.")
            else:
                print("❌ Evolution failed.")
        else:
            print(f"⏳ Not ready for evolution. Need {0.8 - progress:.1%} more progress.")
            print("💡 Try running more training sessions or assessments.")
    
    async def reset(self, args):
        """Reset learning system"""
        if not args.confirm:
            print("⚠️ This will reset the entire learning system!")
            print("All progress, metrics, and training history will be lost.")
            confirm = input("Type 'RESET' to confirm: ")
            if confirm != 'RESET':
                print("Reset cancelled.")
                return
        
        print("🔄 Resetting learning system...")
        print("=" * 40)
        
        try:
            await self.system.emergency_learning_reset()
            print("✅ Learning system reset completed.")
            print("StillMe is now back to INFANT stage.")
        except Exception as e:
            logger.error(f"Reset failed: {e}")
            print(f"❌ Reset failed: {e}")
    
    async def export(self, args):
        """Export learning data"""
        output_file = args.output or f"learning_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        print(f"📤 Exporting learning data to {output_file}...")
        print("=" * 40)
        
        try:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'system_status': self.system.get_learning_status(),
                'training_sessions': [asdict(session) for session in self.system.training_sessions],
                'performance_history': list(self.system.performance_history),
                'config': asdict(self.system.config)
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Data exported to {output_file}")
            print(f"Exported {len(self.system.training_sessions)} training sessions")
            print(f"Exported {len(self.system.performance_history)} performance records")
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            print(f"❌ Export failed: {e}")
    
    async def _custom_training_session(self, args):
        """Run custom training session"""
        # This would implement custom training based on args
        # For now, just run daily session
        return await self.system.daily_learning_session()

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="StillMe Evolutionary Learning System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status                    # Show current status
  %(prog)s train --session-type daily # Run daily training
  %(prog)s assess --type full        # Run full assessment
  %(prog)s evolve --force            # Force evolution
  %(prog)s reset --confirm           # Reset system
  %(prog)s export --output data.json # Export learning data
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show learning system status')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Run training session')
    train_parser.add_argument('--session-type', choices=['daily', 'custom'], 
                             help='Type of training session')
    
    # Assess command
    assess_parser = subparsers.add_parser('assess', help='Run self-assessment')
    assess_parser.add_argument('--type', choices=['full', 'quick'], 
                              help='Type of assessment')
    
    # Evolve command
    evolve_parser = subparsers.add_parser('evolve', help='Trigger evolution')
    evolve_parser.add_argument('--force', action='store_true',
                              help='Force evolution even if not ready')
    
    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Reset learning system')
    reset_parser.add_argument('--confirm', action='store_true',
                             help='Skip confirmation prompt')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export learning data')
    export_parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create CLI instance and run command
    cli = EvolutionaryLearningCLI()
    
    try:
        if args.command == 'status':
            asyncio.run(cli.status(args))
        elif args.command == 'train':
            asyncio.run(cli.train(args))
        elif args.command == 'assess':
            asyncio.run(cli.assess(args))
        elif args.command == 'evolve':
            asyncio.run(cli.evolve(args))
        elif args.command == 'reset':
            asyncio.run(cli.reset(args))
        elif args.command == 'export':
            asyncio.run(cli.export(args))
    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
    except Exception as e:
        logger.error(f"CLI error: {e}")
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
