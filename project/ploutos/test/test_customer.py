CUSTOMER_ID = 1
CUSTOMER = 'testcustomer1'
MIGRATION = 'test_migration_one'

class TestCustomer(testing.Test):

	def setUp(self):
		self.add_option("-c","--customer",default=CUSTOMER,help="Customer username from model.")
		self.add_option("-i","--id",default=CUSTOMER_ID,help="Customer ID from model.")
		self.add_option("-m","--migration",default=MIGRATION,help="Migration code name.")
		self.arguments()

	@unittest.expectedFailure
	def test_get_customer_noparams(self):
		self.customer = customer.Customer()

	@unittest.expectedFailure
	def test_get_customer_badid(self):
		bad_id = self.random_string(20)
		self.customer = customer.Customer(id=self.random_string(20))

	@unittest.expectedFailure
	def test_get_customer_fakeid(self):
		self.customer = customer.Customer(id=0)

	@unittest.expectedFailure
	def test_get_customer_fakeparams(self):
		self.customer = customer.Customer(username=self.random_string(20))

	def test_customer_bydetails(self):
		self.customer = customer.Customer(migration=self.args.migration,username=self.args.username)

	def test_customer_byid(self):
		self.customer = customer.Customer(id=self.args.id)

if __name__ == '__main__':
	unittest.main()
