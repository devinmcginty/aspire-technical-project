Description
---
I implemented the generator as a JSON API hosted on Google Cloud.

The raw JSON data from the database can be retrieved by accessing the root URI:
```
curl https://aspire-ca3d0.uc.r.appspot.com/
```
Mutations can be applied by `POST`ing to `/mutate` with the `_id` of the desired document as a query parameter and the desired mutation as the text body of the request. For ease of use the API doesn't expect the `Content-Type` header to be set to indicate that the request is JSON.
```
curl -X POST https://aspire-ca3d0.uc.r.appspot.com/mutate?id=1 \
-d '{ "posts": [{"_id": 3, "mentions": [ {"_id": 5, "text": "pear"}]}] }'
```
This endpoint performs the mutation on the backend and returns the update statement if everything works correctly. If a problem is encountered it will return a message in the format of `{"error": "[error message]"}`.

The database can be reset by posting to the `/reset` endpoint. This returns the JSON of the now-reset database.
```
curl -X POST https://aspire-ca3d0.uc.r.appspot.com/reset
```

Explanation of Engineering Approach
---
The application was written as a Flask app using Python 3. Most of the deployment was handled in Google Cloud; the database uses Firebase's realtime database, the app image was built using Cloud Build, and the app is served in App Engine using Gunicorn as the WSGI.

Most of the logic of the application exists within `app/src/mutate.py`. This is where the `generate_update_statement` function exists, but most of the heavy lifting is done by the `Document` class in the same file. As a mutation may contain multiple operations (of add, update, or delete), I decided to split these into individual "transactions". The `apply_mutations` method parses the mutation JSON and delegates the transactions appropriately to `apply_add`, `apply_update`, `apply_delete`, or creating a subdocument and passing on the mutation appropriately.

One output from my program that differs from the prompt is regarding a mutation that has multiple types of operations. The prompt presented the output as a single object with keys for `$add`, `$update`, and `$delete`. For most purposes this should be sufficient, especially given the provided assumption that the program shouldn't account for multiple conflicting statements that modify the same document. However, this wouldn't work if there are multiple non-conflicting statements, such as adding 2 posts at once as the `$add` key needs to be unique. Plus (although this likely wouldn't matter) the object doesn't preserve the order of the operations as JSON objects are unordered. Therefore, I chose to output the command as an array of objects. The downside of this is that the output of applying a mutation may be either an object or array, which could possibly cause typing issues for whatever consumes the endpoint. However, I feel like the best approach to keep the output type consistent would be to default to always returning an array, with single-operation mutations being an array of only one object.

Though the prompt said to account for any number of nested levels, I chose to limit the depth to 128 levels which can be altered via a `RECURSION_LIMIT` value. I chose this value arbitrarily to prevent excess memory usage. Also, the maximum  nesting depth in the examples never exceeded 4 or 5 levels, so this felt adequate. That being said, I believe the actual recursion limit could be reworked to closer to 1000 or more if necessary via some clever use of data redistribution without negatively impacting performance.

Testing was handled via Pytest with the tests existing in `app/src/test_mutation.py`.

Things I Would Add
---
When I first started working on this I intended to create a front-end interface, but after some experimentation I realized that the API endpoints made more sense on their own.

One change that I would try to design would be to validate an entire mutation before running it, and then executing it as a batch operation. As currently written the program would run each transaction sequentially and then throw an error if one is encountered, which wouldn't include an indication on what operations succeeded.

If this was something that I planned on developing further the first things I'd set up would be an automated testing and deployment pipeline, likely using Github Actions. Additionally, while I found Firebase's real time database to be useful for rapid prototyping, there were some issues that I had regarding N+1 queries or overly-complicated queries that could have been avoided by using a combination of databases. If I was to build something like this for public use I would likely use a combination of a document-oriented database and a relational database, likely Elasticsearch and Postgres.

One thing that I didn't account for when I started this project is that Firebase doesn't allow keys to have false-y values other than `false`, which includes empty strings, empty lists, `NULL`, etc. Thus, some data is represented differently in the database compared to the original schema. If this caused issues it could be worked around with the data restructure in the previous paragraph, or handling empty values in the code.

Because of the nature of how the JSON inputs and outputs are formatted there could be issues if this was a user-facing API. For example, it wouldn't be possible to add a subdocument that had `_delete` as a legitimate key. Also, keys containing full stops would cause the resulting update message to seem like it has additional layers of depth in the data. However, these possible edge cases were part of the original design rather than the implementation.

I built this prioritizing simplicity without much concern for security or stability. In a production setting I would set the Firebase private key as a Docker secret, a job queue to handle larger and more complex mutations, and some sort of way to limit access to the API endpoints as all write/read operations are currently completely public. The tests could also be expanded a lot, with additional tests written for the individual transaction methods, testing the interface with Firebase, and other miscellaneous tests like static linting.
