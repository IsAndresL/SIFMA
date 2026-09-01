from flask import request, jsonify, session
from core.security import SecurityService
from application.services import ConclusionApplicationService
from . import api_bp

conclusion_service = ConclusionApplicationService()

@api_bp.route('/api/agronomic_conclusions', methods=['GET', 'POST'])
def handle_agronomic_conclusions():
    if request.method == 'GET':
        plant_id = request.args.get('plant_id', session.get('active_plant_id', 1))
        date_str = request.args.get('date_str')
        period_type = request.args.get('period_type')
        
        conclusions = conclusion_service.get_conclusions(int(plant_id), date_str, period_type)
        return jsonify({
            "status": "success",
            "count": len(conclusions),
            "conclusions": [c.to_dict() for c in conclusions]
        })
        
    elif request.method == 'POST':
        data = request.json or {}
        date_str = SecurityService.sanitize_text(data.get('date_str', ''), 30)
        general_conclusion = SecurityService.sanitize_text(data.get('general_conclusion', ''), 2000)
        
        if not date_str or not general_conclusion:
            return jsonify({"status": "error", "message": "La fecha y la conclusión general son requeridas."}), 400
            
        plant_id = data.get('plant_id') or session.get('active_plant_id', 1)
        payload = {
            "plant_id": int(plant_id),
            "date_str": date_str,
            "period_type": SecurityService.sanitize_text(data.get('period_type', 'diario'), 30),
            "growth_obs": SecurityService.sanitize_text(data.get('growth_obs', ''), 1000),
            "climate_obs": SecurityService.sanitize_text(data.get('climate_obs', ''), 1000),
            "nutrition_obs": SecurityService.sanitize_text(data.get('nutrition_obs', ''), 1000),
            "general_conclusion": general_conclusion,
            "author": SecurityService.sanitize_text(data.get('author', 'Investigador SIFMA'), 100)
        }
        
        new_note = conclusion_service.create_conclusion(payload)
        return jsonify({
            "status": "success",
            "message": "Conclusión agronómica guardada con éxito.",
            "note": new_note.to_dict()
        })

@api_bp.route('/api/agronomic_conclusions/<int:note_id>', methods=['DELETE'])
def delete_agronomic_conclusion(note_id: int):
    success = conclusion_service.delete_conclusion(note_id)
    if not success:
        return jsonify({"status": "error", "message": "Nota no encontrada."}), 404
        
    return jsonify({"status": "success", "message": "Conclusión eliminada exitosamente."})
