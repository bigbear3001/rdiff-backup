import unittest, os, time
from commontest import *
from rdiff_backup import Globals, rpath, fs_abilities

class FSAbilitiesTest(unittest.TestCase):
	"""Test testing of file system abilities

	Some of these tests assume that the actual file system tested has
	the given abilities.  If the file system this is run on differs
	from the original test system, this test may/should fail. Change
	the expected values below.

	"""
	# Describes standard linux file system without acls/eas
	dir_to_test = abs_test_dir
	eas = acls = 1
	chars_to_quote = ""
	extended_filenames = 1
	case_sensitive = 1
	ownership = (os.getuid() == 0)
	hardlinks = fsync_dirs = 1
	dir_inc_perms = 1
	resource_forks = 0
	carbonfile = 0
	high_perms = 1

	# Describes MS-Windows style file system
	#dir_to_test = "/mnt/fat"
	#eas = acls = 0
	#extended_filenames = 0
	#chars_to_quote = "^a-z0-9_ -"
	#ownership = hardlinks = 0
	#fsync_dirs = 1
	#dir_inc_perms = 0
	#resource_forks = 0
	#carbonfile = 0

	# A case insensitive directory (FIXME must currently be created by root)
	# mkdir build/testfiles/fs_insensitive
	# dd if=/dev/zero of=build/testfiles/fs_fatfile.dd bs=512 count=1024
	# mkfs.fat build/testfiles/fs_fatfile.dd
	# sudo mount -o loop,uid=$(id -u) build/testfiles/fs_fatfile.dd build/testfiles/fs_insensitive
	# touch build/testfiles/fs_fatfile.dd build/testfiles/fs_insensitive/some_File

	case_insensitive_path = os.path.join(abs_test_dir, 'fs_insensitive')

	def testReadOnly(self):
		"""Test basic querying read only"""
		base_dir = rpath.RPath(Globals.local_connection, self.dir_to_test)
		fsa = fs_abilities.FSAbilities('read-only').init_readonly(base_dir)
		print(fsa)
		assert fsa.read_only == 1, fsa.read_only
		assert fsa.eas == self.eas, fsa.eas
		assert fsa.acls == self.acls, fsa.acls
		assert fsa.resource_forks == self.resource_forks, fsa.resource_forks
		assert fsa.carbonfile == self.carbonfile, fsa.carbonfile
		assert fsa.case_sensitive == self.case_sensitive, fsa.case_sensitive

	def testReadWrite(self):
		"""Test basic querying read/write"""
		base_dir = rpath.RPath(Globals.local_connection, self.dir_to_test)
		new_dir = base_dir.append("fs_abilitiestest")
		if new_dir.lstat(): Myrm(new_dir.path)
		new_dir.setdata()
		new_dir.mkdir()
		t = time.time()
		fsa = fs_abilities.FSAbilities('read/write').init_readwrite(new_dir)
		print("Time elapsed = ", time.time() - t)
		print(fsa)
		assert fsa.read_only == 0, fsa.read_only
		assert fsa.eas == self.eas, fsa.eas
		assert fsa.acls == self.acls, fsa.acls
		assert fsa.ownership == self.ownership, fsa.ownership
		assert fsa.hardlinks == self.hardlinks, fsa.hardlinks
		assert fsa.fsync_dirs == self.fsync_dirs, fsa.fsync_dirs
		assert fsa.dir_inc_perms == self.dir_inc_perms, fsa.dir_inc_perms
		assert fsa.resource_forks == self.resource_forks, fsa.resource_forks
		assert fsa.carbonfile == self.carbonfile, fsa.carbonfile
		assert fsa.high_perms == self.high_perms, fsa.high_perms
		assert fsa.extended_filenames == self.extended_filenames

		#ctq_rp = new_dir.append("chars_to_quote")
		#assert ctq_rp.lstat()
		#fp = ctq_rp.open('rb')
		#chars_to_quote = fp.read()
		#assert not fp.close()
		#assert chars_to_quote == self.chars_to_quote, chars_to_quote

		new_dir.delete()

	@unittest.skipUnless(os.path.isdir(case_insensitive_path),
				"Case insensitive directory %s does not exist" %
					case_insensitive_path)
	def test_case_sensitive(self):
		"""Test a read-only case-INsensitive directory"""
		rp = rpath.RPath(Globals.local_connection, self.case_insensitive_path)
		fsa = fs_abilities.FSAbilities('read-only')
		fsa.set_case_sensitive_readonly(rp)
		assert fsa.case_sensitive == 0, fsa.case_sensitive

if __name__ == "__main__": unittest.main()

