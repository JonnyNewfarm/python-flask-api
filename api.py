from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, reqparse, fields, marshal_with, abort

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
api = Api(app)


class QuoteModel(db.Model):
    __tablename__ = 'quote_model'
    id = db.Column(db.Integer, primary_key=True)
    quote = db.Column(db.String(100), unique=True, nullable=False)
    vote = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"Quote(name={self.quote}, vote={self.vote})"


class VoteModel(db.Model):
    __tablename__ = 'vote_model'
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey(
        'quote_model.id'), nullable=False)
    ip_address = db.Column(db.String(50), nullable=False)

    __table_args__ = (db.UniqueConstraint(
        'quote_id', 'ip_address', name='unique_vote_per_ip'),)


create_quote_args = reqparse.RequestParser()
create_quote_args.add_argument(
    'quote', type=str, required=True, help="Quote cannot be blank")

resource_fields = {
    'id': fields.Integer,
    'quote': fields.String,
    'vote': fields.Integer,
}


class Quotes(Resource):
    @marshal_with(resource_fields)
    def get(self):
        quotes = QuoteModel.query.all()
        return quotes

    @marshal_with(resource_fields)
    def post(self):
        args = create_quote_args.parse_args()
        quote = QuoteModel(quote=args['quote'], vote=0)
        db.session.add(quote)
        db.session.commit()
        return quote, 201


class Vote(Resource):
    @marshal_with(resource_fields)
    def post(self, id):
        quote = QuoteModel.query.get(id)
        if not quote:
            abort(404, message="Quote not found")

        ip_address = request.remote_addr or 'unknown'
        existing_vote = VoteModel.query.filter_by(
            quote_id=id, ip_address=ip_address).first()
        if existing_vote:
            abort(403, message="You have already voted for this quote")

        vote_record = VoteModel(quote_id=id, ip_address=ip_address)
        db.session.add(vote_record)

        quote.vote += 1
        db.session.commit()
        return quote, 200


api.add_resource(Quotes, '/api/quotes')
api.add_resource(Vote, '/api/quotes/<int:id>')


@app.route('/')
def home():
    return '<h1>Welcome to the Quotes API</h1>'


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
