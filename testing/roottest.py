import unittest, os
from commontest import *
from rdiff_backup import Globals

"""Root tests - contain tests which need to be run as root.

Some of the quoting here may not work with csh (works on bash).  Also,
if you aren't me, check out the 'user' global variable.

"""

Globals.set('change_source_perms', None)
Globals.counter = 0
verbosity = 1
Log.setverbosity(verbosity)

assert os.getuid() == 0, "Run this test as root!"

# we need a normal user for our test, we use environment variables to use
# the right one, either through SUDO_* variables set by sudo, or set
# explicitly by the tester.
userid = int(os.getenv('RDIFF_TEST_UID', os.getenv('SUDO_UID')))
user = os.getenv('RDIFF_TEST_USER', os.getenv('SUDO_USER'))
assert userid, "Unable to assess ID of non-root user to be used for tests"
assert user, "Unable to assess name of non-root user to be used for tests"


def Run(cmd):
	print("Running: ", cmd)
	rc = os.system(cmd)
	assert not rc, "Command `%s` failed with rc=%d" % (cmd, rc)

class RootTest(unittest.TestCase):
	dirlist1 = [os.path.join(old_test_dir, "root"),
			os.path.join(old_test_dir, "various_file_types"),
			os.path.join(old_test_dir, "increment4")]
	dirlist2 = [os.path.join(old_test_dir, "increment4"),
			os.path.join(old_test_dir, "root"),
			os.path.join(old_test_dir, "increment1")]
	def testLocal1(self):
		BackupRestoreSeries(1, 1, self.dirlist1, compare_ownership = 1)
	def testLocal2(self):
		BackupRestoreSeries(1, 1, self.dirlist2, compare_ownership = 1)
	def testRemote(self):
		BackupRestoreSeries(None, None, self.dirlist1, compare_ownership = 1)

	def test_ownership(self):
		"""Test backing up and restoring directory with different uids

		This checks for a bug in 0.13.4 where uids and gids would not
		be restored correctly.

		Also test to make sure symlinks get the right ownership.
		(Earlier symlink ownership was not preserved.)

		"""
		dirrp = rpath.RPath(Globals.local_connection,
				os.path.join(abs_test_dir, "root_owner"))
		def make_dir():
			re_init_rpath_dir(dirrp)
			rp1 = dirrp.append('file1')
			rp2 = dirrp.append('file2')
			rp3 = dirrp.append('file3')
			rp4 = dirrp.append('file4')
			rp5 = dirrp.append('symlink')
			rp1.touch()
			rp2.touch()
			rp3.touch()
			rp4.touch()
			rp5.symlink('foobar')
			rp1.chown(2000, 2000)
			rp2.chown(2001, 2001)
			rp3.chown(2002, 2002)
			rp4.chown(2003, 2003)
			rp5.chown(2004, 2004)
		make_dir()
		dirlist = [os.path.join(abs_test_dir, "root_owner"),
				os.path.join(old_test_dir, "empty"),
				os.path.join(abs_test_dir, "root_owner")]
		BackupRestoreSeries(1, 1, dirlist, compare_ownership = 1)
		symrp = rpath.RPath(Globals.local_connection,
						os.path.join(abs_output_dir, 'symlink'))
		assert symrp.issym(), symrp
		assert symrp.getuidgid() == (2004, 2004), symrp.getuidgid()

	def test_ownership_mapping(self):
		"""Test --user-mapping-file and --group-mapping-file options"""
		def write_ownership_dir():
			"""Write the directory testfiles/root_mapping"""
			rp = rpath.RPath(Globals.local_connection,
						os.path.join(abs_test_dir, "root_mapping"))
			re_init_rpath_dir(rp)
			rp1 = rp.append('1')
			rp1.touch()
			rp2 = rp.append('2')
			rp2.touch()
			rp2.chown(userid, 1) # use groupid 1, usually bin
			return rp

		def write_mapping_files(dir_rp):
			"""Write user and group mapping files, return paths"""
			user_map_rp = dir_rp.append('user_map')
			group_map_rp = dir_rp.append('group_map')
			user_map_rp.write_string('root:%s\n%s:root' % (user, user))
			group_map_rp.write_string('0:1')
			return user_map_rp.path, group_map_rp.path

		def get_ownership(dir_rp):
			"""Return pair (ids of dir_rp/1, ids of dir_rp2) of ids"""
			rp1, rp2 = list(map(dir_rp.append, ('1', '2')))
			assert rp1.isreg() and rp2.isreg(), (rp1.isreg(), rp2.isreg())
			return (rp1.getuidgid(), rp2.getuidgid())

		in_rp = write_ownership_dir()
		user_map, group_map = write_mapping_files(in_rp)
		out_rp = rpath.RPath(Globals.local_connection, abs_output_dir)
		if out_rp.lstat(): Myrm(out_rp.path)

		assert get_ownership(in_rp) == ((0,0), (userid, 1)), \
			   get_ownership(in_rp)
		rdiff_backup(1, 0, in_rp.path, out_rp.path,
					 extra_options = ("--user-mapping-file %s "
									  "--group-mapping-file %s" %
									  (user_map, group_map)))
		assert get_ownership(out_rp) == ((userid, 0), (0, 1)), \
			   get_ownership(out_rp)

	def test_numerical_mapping(self):
		"""Test --preserve-numerical-ids option

		This doesn't really test much, since we don't have a
		convenient system with different uname/ids.

		"""
		def write_ownership_dir():
			"""Write the directory testfiles/root_mapping"""
			rp = rpath.RPath(Globals.local_connection,
						os.path.join(abs_test_dir, "root_mapping"))
			re_init_rpath_dir(rp)
			rp1 = rp.append('1')
			rp1.touch()
			rp2 = rp.append('2')
			rp2.touch()
			rp2.chown(userid, 1) # use groupid 1, usually bin
			return rp
		
		def get_ownership(dir_rp):
			"""Return pair (ids of dir_rp/1, ids of dir_rp2) of ids"""
			rp1, rp2 = list(map(dir_rp.append, ('1', '2')))
			assert rp1.isreg() and rp2.isreg(), (rp1.isreg(), rp2.isreg())
			return (rp1.getuidgid(), rp2.getuidgid())

		in_rp = write_ownership_dir()
		out_rp = rpath.RPath(Globals.local_connection, abs_output_dir)
		if out_rp.lstat(): Myrm(out_rp.path)

		assert get_ownership(in_rp) == ((0,0), (userid, 1)), \
			   get_ownership(in_rp)
		rdiff_backup(1, 0, in_rp.path, out_rp.path,
					 extra_options = ("--preserve-numerical-ids"))
		assert get_ownership(out_rp) == ((0,0), (userid, 1)), \
			   get_ownership(in_rp)

	def tearDown(self):
		# especially the logfile might still appear opened if a test was interrupted
		Main.cleanup()



class HalfRoot(unittest.TestCase):
	"""Backing up files where origin is root and destination is non-root"""
	def make_dirs(self):
		"""Make source directories, return rpaths

		These make a directory with a changing file that is not
		self-readable.  (Caused problems earlier.)

		"""
		rp1 = rpath.RPath(Globals.local_connection,
						os.path.join(abs_test_dir, "root_half1"))
		re_init_rpath_dir(rp1)
		rp1_1 = rp1.append('foo')
		rp1_1.write_string('hello')
		rp1_1.chmod(0)
		rp1_2 = rp1.append('to be deleted')
		rp1_2.write_string('aosetuhaosetnuhontu')
		rp1_2.chmod(0)
		rp1_3 = rp1.append('unreadable_dir')
		rp1_3.mkdir()
		rp1_3_1 = rp1_3.append('file_inside')
		rp1_3_1.write_string('blah')
		rp1_3_1.chmod(0)
		rp1_3_2 = rp1_3.append('subdir_inside')
		rp1_3_2.mkdir()
		rp1_3_2_1 = rp1_3_2.append('foo')
		rp1_3_2_1.write_string('saotnhu')
		rp1_3_2_1.chmod(0)
		rp1_3_2.chmod(0)
		rp1_3.chmod(0)

		rp2 = rpath.RPath(Globals.local_connection,
						os.path.join(abs_test_dir, "root_half2"))
		re_init_rpath_dir(rp2)
		rp2_1 = rp2.append('foo')
		rp2_1.write_string('goodbye')
		rp2_1.chmod(0)
		rp2_3 = rp2.append('unreadable_dir')
		rp2_3.mkdir()
		rp2_3_1 = rp2_3.append('file_inside')
		rp2_3_1.write_string('new string')
		rp2_3_1.chmod(0)
		rp2_3_2 = rp2_3.append('subdir_inside')
		rp2_3_2.mkdir()
		rp2_3_2_1 = rp2_3_2.append('foo')
		rp2_3_2_1.write_string('asoetn;oet')
		rp2_3_2_1.chmod(0)
		rp2_3_2.chmod(0)
		rp2_3_3 = rp2_3.append('file2')
		rp2_3_3.touch()
		rp2_3.chmod(0)
		# The rp_2_4 below test for a perm error, also tested in
		# regressiontest.py testConfig1
		rp2_4 = rp2.append('test2')
		rp2_4.mkdir()
		rp2_4_1 = rp2_4.append('1-dir')
		rp2_4_1.mkdir()
		reg2_4_1_1 = rp2_4_1.append('reg')
		reg2_4_1_1.touch()
		reg2_4_1_1.chmod(0)
		rp2_4_1.chmod(0)
		reg2_4_2 = rp2_4.append('2-reg')
		reg2_4_2.touch()
		reg2_4_2.chmod(0)
		rp2_4.chmod(0)

		return rp1, rp2

	def cause_regress(self, rp):
		"""Change some of the above to trigger regress"""
		rp1_1 = rp.append('foo')
		rp1_1.chmod(0o4)
		rp_new = rp.append('lala')
		rp_new.write_string('asoentuh')
		rp_new.chmod(0)
		assert not os.system('chown %s %s' % (user, rp_new.path))
		rp1_3 = rp.append('unreadable_dir')
		rp1_3.chmod(0o700)
		rp1_3_1 = rp1_3.append('file_inside')
		rp1_3_1.chmod(0o1)
		rp1_3.chmod(0)
		
		rbdir = rp.append('rdiff-backup-data')
		rbdir.append('current_mirror.2000-12-31T21:33:20-07:00.data').touch()

	def test_backup(self):
		"""Test back up, simple restores"""
		in_rp1, in_rp2 = self.make_dirs()
		outrp = rpath.RPath(Globals.local_connection, abs_output_dir)
		re_init_rpath_dir(outrp, userid)
		remote_schema = 'su -c "rdiff-backup --server" %s' % (user,)
		cmd_schema = ("rdiff-backup -v" + str(verbosity) +
					  " --current-time %s --remote-schema '%%s' %s '%s'::%s")

		cmd1 = cmd_schema % (10000, in_rp1.path, remote_schema, outrp.path)
		Run(cmd1)
		in_rp1.setdata()
		outrp.setdata()

		cmd2 = cmd_schema % (20000, in_rp2.path, remote_schema, outrp.path)
		Run(cmd2)
		in_rp2.setdata()
		outrp.setdata()
		#assert CompareRecursive(in_rp2, outrp)

		rout_rp = rpath.RPath(Globals.local_connection, abs_restore_dir)
		restore_schema = ("rdiff-backup -v" + str(verbosity) +
						  " -r %s --remote-schema '%%s' '%s'::%s %s")
		Myrm(rout_rp.path)
		cmd3 = restore_schema % (10000, remote_schema, outrp.path,
								 rout_rp.path)
		Run(cmd3)
		assert CompareRecursive(in_rp1, rout_rp)
		rout_perms = rout_rp.append('unreadable_dir').getperms()
		outrp_perms = outrp.append('unreadable_dir').getperms()
		assert rout_perms == 0, rout_perms
		assert outrp_perms == 0, outrp_perms

		Myrm(rout_rp.path)
		cmd4 = restore_schema % ("now", remote_schema, outrp.path,
								 rout_rp.path)
		Run(cmd4)
		assert CompareRecursive(in_rp2, rout_rp)
		rout_perms = rout_rp.append('unreadable_dir').getperms()
		outrp_perms = outrp.append('unreadable_dir').getperms()
		assert rout_perms == 0, rout_perms
		assert outrp_perms == 0, outrp_perms

		self.cause_regress(outrp)
		cmd5 = ('su -c "rdiff-backup --check-destination-dir %s" %s' %
				(outrp.path, user))
		Run(cmd5)


class NonRoot(unittest.TestCase):
	"""Test backing up as non-root user

	Test backing up a directory with files of different userids and
	with device files in it, as a non-root user.  When restoring as
	root, everything should be restored normally.

	"""
	def make_root_dirs(self):
		"""Make directory createable only by root"""
		rp = rpath.RPath(Globals.local_connection,
						os.path.join(abs_test_dir, "root_out1"))
		re_init_rpath_dir(rp)
		rp1 = rp.append("1")
		rp1.touch()
		rp2 = rp.append("2")
		rp2.touch()
		rp2.chown(1, 1)
		rp3 = rp.append("3")
		rp3.touch()
		rp3.chown(2, 2)
		rp4 = rp.append("dev")
		rp4.makedev('c', 4, 28)

		sp = rpath.RPath(Globals.local_connection,
						os.path.join(abs_test_dir, "root_out2"))
		if sp.lstat(): Myrm(sp.path)
		Run("cp -a %s %s" % (rp.path, sp.path))
		rp2 = sp.append("2")
		rp2.chown(2, 2)
		rp3 = sp.append("3")
		rp3.chown(1, 1)
		assert not CompareRecursive(rp, sp, compare_ownership = 1)

		return rp, sp

	def backup(self, input_rp, output_rp, time):
		global user
		backup_cmd = ("rdiff-backup --no-compare-inode "
					  "--current-time %s %s %s" %
					  (time, input_rp.path, output_rp.path))
		Run("su %s -c '%s'" % (user, backup_cmd))

	def restore(self, dest_rp, restore_rp, time = None):
		Myrm(restore_rp.path)
		if time is None: time = "now"
		restore_cmd = "rdiff-backup -r %s %s %s" % (time, dest_rp.path,
													restore_rp.path,)
		Run(restore_cmd)		

	def test_non_root(self):
		"""Main non-root -> root test"""
		input_rp1, input_rp2 = self.make_root_dirs()
		Globals.change_ownership = 1
		output_rp = rpath.RPath(Globals.local_connection, abs_output_dir)
		re_init_rpath_dir(output_rp, userid)
		restore_rp = rpath.RPath(Globals.local_connection, abs_restore_dir)
		empty_rp = rpath.RPath(Globals.local_connection,
						os.path.join(old_test_dir, "empty"))

		self.backup(input_rp1, output_rp, 1000000)
		self.restore(output_rp, restore_rp)
		assert CompareRecursive(input_rp1, restore_rp, compare_ownership = 1)

		self.backup(input_rp2, output_rp, 2000000)
		self.restore(output_rp, restore_rp)
		assert CompareRecursive(input_rp2, restore_rp, compare_ownership = 1)

		self.backup(empty_rp, output_rp, 3000000)
		self.restore(output_rp, restore_rp)
		assert CompareRecursive(empty_rp, restore_rp, compare_ownership = 1)

		self.restore(output_rp, restore_rp, 1000000)
		assert CompareRecursive(input_rp1, restore_rp, compare_ownership = 1)

		self.restore(output_rp, restore_rp, 2000000)
		assert CompareRecursive(input_rp2, restore_rp, compare_ownership = 1)


if __name__ == "__main__": unittest.main()
