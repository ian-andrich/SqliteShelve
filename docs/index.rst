.. SqliteShelve documentation master file, created by
   sphinx-quickstart on Sat Apr 10 17:55:07 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to SqliteShelve's documentation!
========================================

SqliteShelve is a Simple KV Store backed by Sqlite3.  No setup or configuration needed.

This module gives you access to a sqlite3 backed shelf using only core python components.

It has been written because the shelf backends are hard to install/configure on Windows.
Further, the dumb backend is slow.
10 insertions / second slow on my machine with an SSD drive.

This module gets close to 70,000 insertions per second writing to disk.
Individual key lookups reach about 10,000 key lookups per second reading from disk.

Where the shelf API is not adhered to it is because, we cannot assume we can fit all data in memory.  
The items and keys methods of the shelf API both assume so.

Examples:

.. testcode::

   from src import SqliteShelve

.. testcode::

   table_name = "machomanrandysavage"
   filename = ":memory:"
   demo_shelf = SqliteShelve(filename, table_name)
   with demo_shelf:
      for num in range(100):
         key = f"{num}"
         val = f"Hello {num}"

         # Load the data into the shelf.
         demo_shelf[key] = val
      print(demo_shelf["42"])
      
      # Delete data from the shelf.
      del demo_shelf["42"]
      try:
         demo_shelf["42"]
      except KeyError:
         print("Key not found!")

      # Key checking works
      assert "1" in demo_shelf

      # Regex search on keys
      # All keys that start with 3 and end in 4
      print(list(demo_shelf.regex(r"^34$")))

.. testoutput::
   
   Hello 42
   Key not found!
   [('34', 'Hello 34')]

.. toctree::
   :maxdepth: 2
   :caption: Contents:


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
