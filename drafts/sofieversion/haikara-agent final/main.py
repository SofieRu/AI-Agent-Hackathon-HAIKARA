"""
Main entry point for Haikara Multi-Agent System
"""
import os
from dotenv import load_dotenv
from orchestrator import HaikaraOrchestrator
from compute_agent import ComputeAgent


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


def main():
    """Main execution function"""
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║        🌟 HAIKARA Multi-Agent System 🌟                   ║
    ║                                                            ║
    ║   Compute-Energy Convergence for DEG Ecosystem            ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # Load configuration
    config = load_config()
    
    # Initialize orchestrator
    orchestrator = HaikaraOrchestrator(config)
    
    # Generate sample workloads for demo
    print("🔧 Generating sample workloads for demonstration...")
    orchestrator.compute_agent.generate_sample_workloads(count=5)
    
    # Run optimization cycle
    try:
        results = orchestrator.run_optimization_cycle()
        
        if results:
            print("\n" + "="*60)
            print("📊 FINAL RESULTS SUMMARY")
            print("="*60)
            print(f"\n✅ Successfully optimized {len(results['schedule'])} workloads")
            print(f"\n💰 Financial Benefits:")
            print(f"   • Cost Savings: £{results['savings']['cost_savings']:.2f}")
            print(f"   • P415 Revenue: £{results['savings']['p415_revenue']:.2f}")
            print(f"   • Total: £{results['savings']['total_benefit']:.2f}")
            print(f"\n🌱 Environmental Impact:")
            print(f"   • Carbon Reduced: {results['savings']['carbon_savings_kg']:.2f} kg CO2")
            print(f"   • Equivalent to: {results['savings']['carbon_savings_kg']/25:.1f} trees planted")
            print(f"\n📝 Audit Trail: audit_trail.json")
            print(f"🔖 Order ID: {results['order_id']}")
            print("\n" + "="*60)
            
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║              ✅ Haikara System Demo Complete               ║
    ║                                                            ║
    ║   Next Steps:                                             ║
    ║   1. Update config.env with real API keys                 ║
    ║   2. Connect to actual BAP Sandbox                        ║
    ║   3. Integrate with real data center workloads            ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()
