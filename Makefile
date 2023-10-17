

sync:
	pipenv sync

run: sync
	pipenv run streamlit run app.py