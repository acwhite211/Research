
class Collaborative_Filtering(object):
	def __init__(self, ratings_matrix, other_views):
		self.ratings_matrix = ratings_matrix

	def recommend(self, user):
