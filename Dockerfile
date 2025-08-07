FROM continuumio/miniconda3:latest

WORKDIR /app

COPY environment.yml .
RUN conda env create -f environment.yml

SHELL ["conda", "run", "-n", "budget-tracker", "/bin/bash", "-c"]

COPY . .

EXPOSE 8501

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "budget-tracker", "streamlit", "run", "app/web/streamlit_app.py", "--server.address=0.0.0.0"]
