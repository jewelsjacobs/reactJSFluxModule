===
GUI
===
-------
hacking
-------
You want to hack on the GUI? The following steps should get you started.

python
------
Create a venv specifically for working on this project. Dependency conflicts may occur if you attempt to use the same venv for multiple projects.

Install the requirements needed for this project. From the top-level of this repository, simply do ``pip install -r requirements.txt -r dev-requirements.txt``.

If you do not have access to the ObjectRocket internal VPN, comment out the line in ``requirements.txt`` which attempts to pull in the ``viper`` package. Run the install command mentioned above. Then, with the core repository cloned on your box, do ``pip install -e /path/to/core``, and now your Python venv should be good to go.

mongodb
-------
Clone the ``devtools`` repository, and run the ``install.sh`` script from the top-level of that repository. This will give you the required MongoDB backend database needed for GUI to function. If you run into any problems during the ``install.sh`` run, consult the README in that repository.

api
---
You may also need to have APIv1 or APIv2 running for certain functionality in GUI. Clone which API repository you may need, and follow installation instructions in the respective repository.

branching
---------
Currently, we are using branches ``master`` and ``develop`` as the main branches in our workflow. When you need to create a new branch, branch off of ``develop``. ``develop`` will be merged back into ``master`` when it is time to cut a new release.

-----
notes
-----
building popovers
-----------------
The element which triggers a popover (probably a button) needs the following attributes:

- Class property "rs-popover-source"
- data-popover="<id of the popover element>"
- data-popover-target="<id of the targeted element for the popover>"
- data-popover-position="<the position the popover will appear relative to the target (right, left, bottom-right, bottom-left)>"

The data popover itself needs to appear in the ``{% block popover %}`` and needs the following attributes:

- Class properties "rs-popover" and "invisible".
- An id corresponding to the popover source data-popover value.

