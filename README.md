To run, use:

```sh
$ pipenv install
```

followed by

```sh
$ pipenv run python pipeline.py [path to webhose JSON file]
```

The output will have many lines of clustering algorithm output, followed by a
JSON blob describing the summary sentences.

If you get error messages about NLTK not being able to find resources, run the following:

```
$ pipenv run python -i
>>> import nltk
>>> nltk.download('stopwords')
>>> nltk.download('punkt')
```
