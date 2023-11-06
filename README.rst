Ranger Radio Transmission Indexer
=================================

.. image:: https://github.com/burningmantech/ranger-transmissions/workflows/CI%2fCD/badge.svg
    :target: https://github.com/burningmantech/ranger-transmissions/actions
    :alt: Build Status
.. image:: https://codecov.io/github/burningmantech/ranger-transmissions/coverage.svg?branch=master
    :target: https://codecov.io/github/burningmantech/ranger-transmissions?branch=master
    :alt: Code Coverage

This software package contains functionality for processing audio from Burning Man's radio system.


Installation
------------

To install this package, you will need to install `Python 3.11`_.
You should also install the `pipx`_ tool, which provides an easy way to install python executables.

Additionally, this package uses the `pydub`_ and the `openai-whisper`_ Python packages, each of which has specific setup requirements.
See the instructions for each package for details.
In particular, both require `ffmpeg`_.

On macOS using `Homebrew`_, you can install what you need thusly:

.. code-block:: console

    brew install python@3.11
    brew install pipx
    brew install ffmpeg

Once you have the above installed, you can install this package using ``pipx``:

.. code-block:: console

    pipx install git+https://github.com/burningmantech/ranger-transmissions.git

You should now have a command called ``rtx`` in your system.


Usage
-----

``rtx`` provides a command line application that lets you browse though indexed audio content.
If you have an existing data file containing an index, put that at ``~/rtx.sqlite``.
Then start the application:

.. code-block:: console

    rtx application


.. _Homebrew: https://brew.sh
.. _ffmpeg: https://ffmpeg.org
.. _openai-whisper: https://github.com/openai/whisper
.. _Python 3.11: https://www.python.org/downloads/release/python-3116/
.. _pipx: https://pypa.github.io/pipx/
.. _pydub: https://github.com/jiaaro/pydub/
