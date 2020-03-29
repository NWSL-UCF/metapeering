python OriginalPeeringAlgorithm.py
tar -cvzf upload.tar.gz affinity.json
curl -F "file=@upload.tar.gz" https://file.io > upload.json