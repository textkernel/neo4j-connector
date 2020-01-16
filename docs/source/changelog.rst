*********
Changelog
*********

1.1.0
=====
* the :code:`run_multiple` connector method now takes the :code:`batch_size` parameter. If the method gets more
  statements than :code:`batch_size` then the statements are split over multiple HTTP requests. The :code:`run_multiple`
  method still returns a single list with the responses from all batches. This parameter can help make large jobs
  manageable for Neo4j (e.g not running out of memory).

1.0.1
=====
* Improved documentation

1.0.0
=====
* Initial release