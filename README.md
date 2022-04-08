

inspired from # Automatic monitor github cve using Github Actions 


## collect

collect certain topic repo in github for auto deploy on vercel or cf worker as idea inspirations

## wordcloud



## auto intro video

https://github.com/sleuth-io/code-video-generator
```
from code_video import CodeScene


class MyScene(CodeScene):
    def construct(self):
        # This does the actual code display and animation
        self.animate_code_comments("readme.md")
    
        # Wait 5 seconds before finishing
        self.wait(5)
```

## auto deploy video



## database

https://github.com/gtalarico/pyairtable


import os

from pyairtable import Table

api_key = os.environ['AIRTABLE_API_KEY']

table = Table(api_key, 'base_id', 'table_name')

table.all()
[ {"id": "rec5eR7IzKSAOBHCz", "fields": { ... }}]

table.create({"Foo": "Bar"})
{"id": "recwAcQdqwe21as", "fields": { "Foo": "Bar" }}]

table.update("recwAcQdqwe21as", {"Foo": "Foo"})
{"id": "recwAcQdqwe21as", "fields": { "Foo": "Foo" }}]

table.delete("recwAcQdqwe21as")
True