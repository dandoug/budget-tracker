FROM condaforge/miniforge3:25.3.1-0

WORKDIR /app

COPY environment.yml .
RUN conda env create -f environment.yml

SHELL ["conda", "run", "-n", "budget-tracker", "/bin/bash", "-c"]

COPY . .

# Remove the full data dir and re-add only the whitelisted files
RUN rm -rf data && mkdir -p data
COPY data/budget_schema.json \
     data/README.md \
     data/sample_budget.yaml \
     data/sample_Simplifi-profit-loss.xlsx \
     data/

# no need to put the tests in the docker container
RUN rm -rf tests

EXPOSE 8501

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "budget-tracker", "streamlit", "run", "app/web/streamlit_app.py", "--server.address=0.0.0.0"]
