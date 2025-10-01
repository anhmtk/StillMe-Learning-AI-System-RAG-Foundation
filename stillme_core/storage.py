"""
StillMe Core Storage
"""

class StateStore:
    """State store for job management"""
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.initialized = False
    
    def initialize(self):
        """Initialize the state store"""
        self.initialized = True
    
    def get_job_step(self, job_id: str, step_id: str):
        """Get job step information"""
        class JobStep:
            def __init__(self):
                self.status = "pending"
                self.error_message = None
        
        return JobStep()
