# Models

Serialized classifier models with corresponding training and testing scripts.
## Directories

* `embedder` - [`FastText`](https://fasttext.cc/) word embedder model for token text vectorization (self-trained, with source)
* `names` - training and test scripts for function name classifiers
* `paths` - training and test scripts for function name classifiers

## Training
Training scripts create a dataset on the fly, perform 5-fold cross-validation and serialize the model.

Usage:
```
cd <names/paths>
python train_<classifier>.py --dbpath="<dataset db path>"
```

## Testing
Testing scripts reconstruct training/test datasets, load a serialized model, make predictions and save the results to a separate results database (model file name is the name of the SQLite table).

Usage:
```
cd <names/paths>
python test.py --dbpath="<dataset db path>" --results="<results db path>" --model="<model file name>"
```

## Files

### Naming
Naming convention for classifier model files:
* function names - `names_<classifier name>.joblib`
* cross-reference paths - `paths_<classifier name>.joblib`

Extensions:
* `*.joblib` - classifier models serialized with [`joblib`](https://pypi.org/project/joblib/)
* `*.ft` - FastText word2vec model serialized with [`gensim.models.FastText`](https://radimrehurek.com/gensim/models/fasttext.html)
