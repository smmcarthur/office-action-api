import requests
import io
from PyPDF2 import PdfReader
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/fetch-office-action', methods=['GET'])
def fetch_office_action():
    serial_number = request.args.get('serial_number')
    if not serial_number:
        return jsonify({'error': 'Serial number is required'}), 400

    url = f"https://tsdr.uspto.gov/ts/cd/casestatus/sn{serial_number}/info.json"
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({
            'error': f'No prosecution history found for serial {serial_number}. '
                     f'This may occur if the application predates USPTO’s electronic records '
                     f'or if the TSDR API does not support this serial number.'
        }), 404

    data = response.json()
    history = data.get("prosecutionHistory", [])
    office_actions = [h for h in history if 'Office Action' in h.get("codeDescription", "")]
    if not office_actions:
        return jsonify({
            'error': 'This application has no recorded office actions available via USPTO’s API.'
        }), 404

    last_action = office_actions[-1]
    doc_url = last_action.get("documentUrl")
    if not doc_url:
        return jsonify({'error': 'Office Action document URL not available from API.'}), 404

    pdf_response = requests.get(doc_url)
    if pdf_response.status_code != 200:
        return jsonify({'error': 'Failed to download Office Action document.'}), 500

    pdf_file = io.BytesIO(pdf_response.content)
    reader = PdfReader(pdf_file)
    text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

    return jsonify({
        'serial_number': serial_number,
        'office_action_text': text[:5000]  # Limit for safety
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

