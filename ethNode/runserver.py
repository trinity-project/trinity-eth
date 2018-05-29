from app import app
import os

ENVIRON=os.environ
if ENVIRON.get("CURRENT_ENVIRON") == "testnet":
    port=21332
else:
    port=21333

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)