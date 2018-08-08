# Explicit Semantic Text Representation Library
This library is being designed with the goal to learn explicit operations over unstructured text.
## Disclaimer
The repository is under heavy development. Here be dragons.
## installation
The project does not provide a stand-alone service as of now, just clone the repository and install via pip to `import` it into your own code.
```bash
git clone http://github.com/semanchester/estrella
cd estrella
pip install -r requirements.txt
pip install .

```

## Minimal Example:
Make sure the [Graphene](http://google.de) service is set up and running.
Create a file "sample.txt" with this content
```text
The chicken crossed the road , because it could .
```
Run this code
```python
#!/usr/bin/env python
from estrella.main import Estrella
main = Estrella()
main.run_pipeline("extended_pipeline", location="sample.txt")
from estrella.serialize.readable.oie import simple_print
facts = main.docs.hop(link_name="facts")
print(simple_print(facts))
from estrella.model.oie import ContextLabel
# Why did the chicken cross the road?
result = facts.filter(subject="The chicken", predicate="cross", object="the road").hop(link_name="links",constraint=lambda link: link.label == ContextLabel.Cause)
print(result.serialize(serialize_with=simple_print))
```
For documentation, refer to the source code.

In general, `Pipeline`s are used to read text and enrich it with external information (such as word embeddings or information extraction). The `default_pipeline` for example, defined in the default config `config/default.conf` will read a plain text file and convert it our internal representation. `extended_pipeline` will do just that and in addition enrich the words with word2vec embeddings and extract information from the text.
`View`s implement operations over collections of `Concept`s, such as `Fact`s and can be serialized to be interpreted by humans or further processed with other tools.