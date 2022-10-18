FROM python:3.9
RUN pip install pandas
COPY server.py /server.py
COPY binlist-data.csv /binlist-data.csv
RUN chmod +x /server.py
CMD python3 server.py 0.0.0.0 53210 example.local
EXPOSE 53210
