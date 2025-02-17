"""regresstest - test the regress module.

Not to be confused with the regression tests.

"""

import unittest
from commontest import *
from rdiff_backup import regress, Time

Log.setverbosity(3)

class RegressTest(unittest.TestCase):
	output_rp = rpath.RPath(Globals.local_connection, abs_output_dir)
	output_rbdir_rp = output_rp.append_path("rdiff-backup-data")
	incrp = []
	for i in range(4):
		incrp.append(rpath.RPath(Globals.local_connection,
				os.path.join(old_test_dir, "increment%d" % (i+1))))

	def runtest(self, regress_function):
		"""Test regressing a full directory to older state

		Make two directories, one with one more backup in it.  Then
		regress the bigger one, and then make sure they compare the
		same.

		Regress_function takes a time and should regress
		self.output_rp back to that time.

		"""
		self.output_rp.setdata()
		if self.output_rp.lstat(): Myrm(self.output_rp.path)

		rdiff_backup(1, 1, self.incrp[0].path, self.output_rp.path,
					 current_time = 10000)
		assert CompareRecursive(self.incrp[0], self.output_rp)

		rdiff_backup(1, 1, self.incrp[1].path, self.output_rp.path,
					 current_time = 20000)
		assert CompareRecursive(self.incrp[1], self.output_rp)

		rdiff_backup(1, 1, self.incrp[2].path, self.output_rp.path,
					 current_time = 30000)
		assert CompareRecursive(self.incrp[2], self.output_rp)

		rdiff_backup(1, 1, self.incrp[3].path, self.output_rp.path,
					 current_time = 40000)
		assert CompareRecursive(self.incrp[3], self.output_rp)

		Globals.rbdir = self.output_rbdir_rp

		regress_function(30000)
		assert CompareRecursive(self.incrp[2], self.output_rp,
								compare_hardlinks = 0)
		regress_function(20000)
		assert CompareRecursive(self.incrp[1], self.output_rp,
								compare_hardlinks = 0)
		regress_function(10000)
		assert CompareRecursive(self.incrp[0], self.output_rp,
								compare_hardlinks = 0)

	def regress_to_time_local(self, time):
		"""Regress self.output_rp to time by running regress locally"""
		self.output_rp.setdata()
		self.output_rbdir_rp.setdata()
		self.add_current_mirror(time)
		regress.Regress(self.output_rp)

	def add_current_mirror(self, time):
		"""Add current_mirror marker at given time"""
		cur_mirror_rp = self.output_rbdir_rp.append(
			"current_mirror.%s.data" % (Time.timetostring(time),))
		cur_mirror_rp.touch()

	def regress_to_time_remote(self, time):
		"""Like test_full above, but run regress remotely"""
		self.output_rp.setdata()
		self.output_rbdir_rp.setdata()
		self.add_current_mirror(time)

		rdiff_backup(False, False, self.output_rp.path, None,
				extra_options="-v3 --check-destination-dir")

	def test_local(self):
		"""Run regress test locally"""
		self.runtest(self.regress_to_time_local)

	def test_remote(self):
		"""Run regress test remotely"""
		self.runtest(self.regress_to_time_remote)

	def test_unreadable(self):
		"""Run regress test when regular file is unreadable"""
		self.output_rp.setdata()
		if self.output_rp.lstat(): Myrm(self.output_rp.path)
		unreadable_rp = self.make_unreadable()

		rdiff_backup(1, 1, unreadable_rp.path, self.output_rp.path,
					 current_time = 1)
		rbdir = self.output_rp.append('rdiff-backup-data')
		marker = rbdir.append('current_mirror.2000-12-31T21:33:20-07:00.data')
		marker.touch()
		self.change_unreadable()

		cmd = "rdiff-backup --check-destination-dir %s" % self.output_rp.path
		print("Executing:", cmd)
		assert not os.system(cmd)

	def make_unreadable(self):
		"""Make unreadable input directory

		The directory needs to be readable initially (otherwise it
		just won't get backed up, and then later we will turn it
		unreadable.

		"""
		rp = rpath.RPath(Globals.local_connection,
				os.path.join(abs_test_dir, "regress"))
		if rp.lstat(): Myrm(rp.path)
		rp.setdata()
		rp.mkdir()
		rp1 = rp.append('unreadable_dir')
		rp1.mkdir()
		rp1_1 = rp1.append('to_be_unreadable')
		rp1_1.write_string('aensuthaoeustnahoeu')
		return rp

	def change_unreadable(self):
		"""Change attributes in directory, so regress will request fp"""
		subdir = self.output_rp.append('unreadable_dir')
		assert subdir.lstat()
		rp1_1 = subdir.append('to_be_unreadable')
		rp1_1.chmod(0)
		subdir.chmod(0)


if __name__ == "__main__": unittest.main()

