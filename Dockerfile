# docker build -t vevor-ble-bridge .
# docker run --privileged --net=host -d vevor-ble-bridge

FROM python:3.11-bookworm
ADD requirements.txt .
RUN pip install --use-pep517 -r requirements.txt
ADD scan.py .
ADD vevor.py .
ADD main.py .
CMD [ "python", "./main.py" ]