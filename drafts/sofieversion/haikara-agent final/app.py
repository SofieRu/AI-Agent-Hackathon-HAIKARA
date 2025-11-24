"""
Web Dashboard for Haikara Multi-Agent System
Flask application to visualize optimization results
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import json
from datetime import datetime
from orchestrator import HaikaraOrchestrator
from dotenv import load_dotenv

app = Flask(__name__, static_folder='static')
CORS(app)

# Global state
orchestrator = None
last_results = None

def load_config():
    """Load configuration from environment file"""
    load_dotenv('config.env')
    
    config = {
        'bap_sandbox_url': os.getenv('BAP_SANDBOX_URL', 'http://localhost:3000/api/v1'),
        'bap_timeout': int(os.getenv('BAP_TIMEOUT', 30)),
        'carbon_api_key': os.getenv('CARBON_INTENSITY_API_KEY'),
        'energy_api_key': os.getenv('OCTOPUS_ENERGY_API_KEY'),
        'max_capacity_kw': float(os.getenv('MAX_COMPUTE_CAPACITY_KW', 1000)),
        'carbon_weight': float(os.getenv('CARBON_WEIGHT', 0.6)),
        'cost_weight': float(os.getenv('COST_WEIGHT', 0.4)),
        'forecast_horizon_hours': int(os.getenv('FORECAST_HORIZON_HOURS', 24)),
        'carbon_cap_kg': float(os.getenv('CARBON_CAP_KG', 500)) if os.getenv('CARBON_CAP_KG') else None
    }
    
    return config

@app.route('/')
def index():
    """Login page"""
    return render_template('login.html')

@app.route('/version-check')
def version_check():
    """Version check page"""
    return render_template('version_check.html')

@app.route('/dashboard')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/run-optimization', methods=['POST'])
def run_optimization():
    """Trigger optimization cycle"""
    global orchestrator, last_results
    
    try:
        # Initialize orchestrator if not exists
        if orchestrator is None:
            config = load_config()
            orchestrator = HaikaraOrchestrator(config)
            
        # Generate sample workloads
        orchestrator.compute_agent.workloads = []  # Clear previous
        orchestrator.compute_agent.generate_sample_workloads(count=5)
        
        # Run optimization
        results = orchestrator.run_optimization_cycle()
        last_results = results
        
        if results:
            # Format results for frontend
            response = {
                'success': True,
                'savings': results['savings'],
                'schedule': [
                    {
                        'job_id': s.job_id,
                        'start': s.scheduled_start.isoformat(),
                        'end': s.scheduled_end.isoformat(),
                        'cost': s.expected_cost,
                        'carbon': s.expected_carbon,
                        'p415_revenue': s.expected_p415_revenue,
                        'score': s.optimization_score
                    }
                    for s in results['schedule']
                ],
                'order_id': results['order_id'],
                'timestamp': datetime.now().isoformat()
            }
            return jsonify(response)
        else:
            return jsonify({'success': False, 'error': 'Optimization failed'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/audit-trail', methods=['GET'])
def get_audit_trail():
    """Get audit trail"""
    try:
        if os.path.exists('audit_trail.json'):
            with open('audit_trail.json', 'r') as f:
                audit_data = json.load(f)
            return jsonify({'success': True, 'audit_trail': audit_data})
        else:
            return jsonify({'success': False, 'error': 'No audit trail found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    global orchestrator, last_results
    
    return jsonify({
        'orchestrator_initialized': orchestrator is not None,
        'last_optimization': last_results is not None,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🌟 Starting Haikara Web Dashboard")
    print("="*60)
    print("\n🌐 Open your browser to: http://localhost:5001")
    print("\n💡 Press Ctrl+C to stop the server\n")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
