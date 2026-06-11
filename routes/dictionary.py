import logging
from flask import Blueprint, render_template, request, jsonify
from models import db, HumanDictionary

logger = logging.getLogger(__name__)

dictionary_bp = Blueprint('dictionary', __name__)


@dictionary_bp.route('/dictionary')
def dictionary():
    """Human词典页面"""
    return render_template('dictionary.html')


@dictionary_bp.route('/api/dictionary')
def get_dictionary():
    """获取词典词条（支持分类筛选和搜索）"""
    category = request.args.get('category', '')
    keyword = request.args.get('keyword', '')

    query = HumanDictionary.query

    if category:
        query = query.filter_by(category=category)

    if keyword:
        query = query.filter(
            db.or_(
                HumanDictionary.term.contains(keyword),
                HumanDictionary.definition.contains(keyword)
            )
        )

    entries = query.order_by(HumanDictionary.category, HumanDictionary.term).all()

    # 获取所有分类
    categories = db.session.query(HumanDictionary.category).distinct().all()
    categories = [c[0] for c in categories]

    return jsonify({
        "success": True,
        "categories": categories,
        "entries": [
            {
                "id": e.id,
                "term": e.term,
                "category": e.category,
                "definition": e.definition,
                "example": e.example,
                "related_terms": e.related_terms
            }
            for e in entries
        ]
    })


@dictionary_bp.route('/api/dictionary/<int:entry_id>')
def get_dictionary_entry(entry_id):
    """获取单个词条详情"""
    entry = db.session.get(HumanDictionary, entry_id)
    if not entry:
        return jsonify({"success": False, "error": "词条不存在"}), 404
    return jsonify({
        "success": True,
        "entry": {
            "id": entry.id,
            "term": entry.term,
            "category": entry.category,
            "definition": entry.definition,
            "example": entry.example,
            "related_terms": entry.related_terms
        }
    })


def init_dictionary():
    """首次启动时导入词典数据"""
    from dictionary_data import DICTIONARY_ENTRIES
    if HumanDictionary.query.first() is None:
        for entry in DICTIONARY_ENTRIES:
            db.session.add(HumanDictionary(**entry))
        db.session.commit()
        logger.info("导入词典数据: %d 条", len(DICTIONARY_ENTRIES))
