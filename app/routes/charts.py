from flask import Blueprint, request, jsonify
import pandas as pd
import logging

charts_bp = Blueprint('charts', __name__)

@charts_bp.route('/generate_static_chart', methods=['POST'])
def generate_static_chart():
    """Generate a static chart image from data"""
    try:
        from app.services.session_service import get_session_manager
        from app.services.response_service import get_response_service
        
        session_manager = get_session_manager()
        response_service = get_response_service()
        
        session_manager.init_session()
        
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
            
        chart_type = data.get('chart_type', 'bar')
        chart_data = data.get('data', [])
        
        if not chart_data:
            return jsonify({"error": "No data provided"}), 400
        
        # Convert data to DataFrame
        df = pd.DataFrame(chart_data)
        
        # Generate the chart using the response formatter
        chart_image = response_service.generate_visualization(df, chart_type)
        
        if chart_image:
            return jsonify({
                "success": True,
                "image_data": chart_image,
                "chart_type": chart_type
            })
        else:
            return jsonify({"error": "Failed to generate chart"}), 500
            
    except Exception as e:
        logging.error(f"Error generating static chart: {e}")
        return jsonify({"error": str(e)}), 500 