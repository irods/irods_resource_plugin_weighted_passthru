import sys
if (sys.version_info >= (2,7)):
    import unittest
else:
    import unittest2 as unittest
import pydevtest_common as pdc
import pydevtest_sessions as s
from resource_suite import ResourceSuite, ShortAndSuite, ResourceBase
import socket
import os
import commands
import shutil
import subprocess
import re


class Test_WeightedPassthru_Resource(unittest.TestCase, ResourceBase):
    hostname = pdc.get_hostname()
    my_test_resource = {
        "setup": [
            "iadmin modresc demoResc name origResc",
            "iadmin mkresc demoResc replication",
            "iadmin mkresc unixA 'unix file system' " + hostname +
                ":" + pdc.get_irods_top_level_dir() + "/unixAVault",
            "iadmin mkresc unixB 'unix file system' " + hostname +
                ":" + pdc.get_irods_top_level_dir() + "/unixBVault",
            "iadmin mkresc w_pt weighted_passthru 'write=1.0;read=1.0'",
            "iadmin addchildtoresc demoResc unixA",
            "iadmin addchildtoresc demoResc w_pt",
            "iadmin addchildtoresc w_pt unixB",
        ],
        "teardown": [
            "iadmin rmchildfromresc w_pt unixB",
            "iadmin rmchildfromresc demoResc w_pt",
            "iadmin rmchildfromresc demoResc unixA",
            "iadmin rmresc unixB",
            "iadmin rmresc unixA",
            "iadmin rmresc demoResc",
            "iadmin rmresc w_pt",
            "iadmin modresc origResc name demoResc",
            "rm -rf " + pdc.get_irods_top_level_dir() + "/unixBVault",
            "rm -rf " + pdc.get_irods_top_level_dir() + "/unixAVault",
        ],
    }

    def setUp(self):
        ResourceBase.__init__(self)
        s.twousers_up()
        self.run_resource_setup()

    def tearDown(self):
        self.run_resource_teardown()
        s.twousers_down()

    def test_weighted_passthrough(self):
        filename = "some_local_file.txt"
        filepath = pdc.create_local_testfile(filename)

        # assertions
        pdc.assertiCmd(s.adminsession, "iput " + filepath)

        # repave a copy in the vault to differentiate
        vaultpath = os.path.join( pdc.get_irods_top_level_dir(), "unixBVault/home/rods", os.path.basename( s.adminsession.sessionDir ), filename )
        subprocess.check_call( "echo 'THISISBROEKN' | cat > %s" % (vaultpath),shell=True)
        
        pdc.assertiCmd(s.adminsession, "iadmin modresc w_pt context 'write=1.0;read=2.0'")
        pdc.assertiCmd(s.adminsession, "iget " + filename + " - ", "LIST", "THISISBROEKN" )

        pdc.assertiCmd(s.adminsession, "iadmin modresc w_pt context 'write=1.0;read=0.01'")
        pdc.assertiCmd(s.adminsession, "iget " + filename + " - ", "LIST", "TESTFILE" )
