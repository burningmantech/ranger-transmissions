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

This package uses the `pydub`_ and `openai-whisper`_ Python packages, each of which has specific setup requirements.
See the instructions for each package for details.
In particular, both require ``ffmpeg``.

On macOS using Homebrew, you can use the following command:

.. code-block:: console

   brew install ffmpeg


.. _pydub: https://github.com/jiaaro/pydub/
.. _whisper: https://github.com/openai/whisper
