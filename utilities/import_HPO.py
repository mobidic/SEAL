#!/usr/bin/env python3
import sys
from pathlib import Path

script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from seal import app, db
from seal.models import Hpo

def extract_hpo_id_from_url(url):
    hpo_id = url.split('/')[-1]
    
    if '_' in hpo_id:
        hpo_id = hpo_id.replace('_', ':')

    return hpo_id

def import_hpo_from_json(json_file_path):
    print(f"📖 Read hpo file : {json_file_path}")

    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    nodes = data.get('graphs', [{}])[0].get('nodes', [])
    print(f"🔍 Find {len(nodes)} HPO terms")

    hpo_data = []
    for node in nodes:
        if node.get('type') != 'CLASS':
            continue

        url = node.get('id', '')
        label = node.get('lbl', '')

        if not url or not label:
            continue

        hpo_id = extract_hpo_id_from_url(url)
        hpo_data.append({
            'hpo': hpo_id,
            'label': label
        })

    print(f"✅ {len(hpo_data)} valid terms")

    with app.app_context():
        existing_hpos = {h.hpo for h in Hpo.query.all()}
        print(f"📊 {len(existing_hpos)} HPO terms in base")

        new_hpos = [h for h in hpo_data if h['hpo'] not in existing_hpos]
        print(f"➕ {len(new_hpos)} new terms to add")

        if not new_hpos:
            print("ℹ️  No new terms")
            return

        batch_size = 1000
        for i in range(0, len(new_hpos), batch_size):
            batch = new_hpos[i:i + batch_size]

            for hpo_item in batch:
                hpo = Hpo(
                    hpo=hpo_item['hpo'],
                    label=hpo_item['label']
                )
                db.session.add(hpo)

            db.session.commit()
            print(f"✅ Batch {i//batch_size + 1} insered ({len(batch)} terms)")

        print(f"🎉 Import Finished ! {len(new_hpos)} HPO terms added")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python import_HPO.py <path_to_hpo.json>")
        sys.exit(1)

    json_file = sys.argv[1]
    import_hpo_from_json(json_file)