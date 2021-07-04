import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    CORS(app)



    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'PATCH,GET,PUT,POST,DELETE,OPTIONS')
        return response


    @app.route('/categories')
    def retrieve_categories():
        categories_body = {}
        allCategories = Category.query.all()
        for cat in allCategories:
            categories_body[cat.id] = cat.type

        if len(categories_body) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'categories': categories_body
        })



    @app.route('/questions')
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        categories = Category.query.all()
        categories_body = {}

        for cat in categories:
            categories_body[cat.id] = cat.type

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(Question.query.all()),
            'categories': categories_body
        })



    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                "success": True,
                "deleted": question_id,
                "total_questions": len(Question.query.all())
            }), 200

        except:
            abort(422)



    @app.route('/questions', methods=['POST'])
    def new_question():

        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_difficulty = body.get('difficulty', None)
        new_category = body.get('category', None)

        search = body.get('searchTerm')

        try:
            if search:
                selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike('%{}%'.format(search))).all()
                current_questions = paginate_questions(request, selection)

                if len(selection) == 0:
                    abort(404)

                return jsonify({
                    "success": True,
                    "questions": current_questions
                }), 200

            else:
                theQuestion = Question(question=new_question, answer=new_answer, difficulty=new_difficulty,
                                       category=new_category)
                theQuestion.insert()

                selection = Question.query.order_by(Question.id).all()
                current_questions = paginate_questions(request, selection)

                return jsonify({
                    'success': True,
                    'created': theQuestion.id,
                    'questions': current_questions,
                    'total_questions': len(Question.query.all())
                })
        except:
            abort(422)



    @app.route('/categories/<int:category_id>/questions')
    def questions_by_categories(category_id):
        category = Category.query.filter_by(id=category_id).one_or_none()

        if category is None:
            abort(400)

        selection = Question.query.filter_by(category=category.id)
        current_questions = paginate_questions(request, selection)

        return jsonify({
            "success": True,
            "category": category.type,
            "questions": current_questions,
            "total_questions": len(Question.query.all())
        })



    @app.route('/quizzes', methods=['POST'])
    def play_the_quiz():

        body = request.get_json()

        category = body.get("quiz_category")
        previous_questions = body.get("previous_questions")
        if (category is None) or (previous_questions is None):
            abort(404)

        if category['id'] != 0:
            questions = Question.query.filter_by(category=category['id']).all()
        else:
            questions = Question.query.all()

        def random_question():
            the_next_question = random.choice(questions).format()
            return the_next_question

        the_next_question = random_question()

        question_asked = False
        if the_next_question['id'] in previous_questions:
            question_asked = True

        while question_asked:
            the_next_question = random.choice(questions).format()

            if len(previous_questions) == len(questions):
                return jsonify({
                    "success": True
                }), 200

        return jsonify({
            "success": True,
            "question": the_next_question
        })




    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Resource not found"
        }), 404

    @app.errorhandler(422)
    def uncrossable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad request"
        }), 400

    @app.errorhandler(405)
    def not_allowed(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "Method not allowed"
        }), 405

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            'success': False,
            'error': 500,
            'message': 'Server error has occurred, please try again'
        }), 500

    return app
