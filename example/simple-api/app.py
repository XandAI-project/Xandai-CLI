from flask import Flask
from flask_restful import Api, Resource, reqparse, abort

# Create Flask app and API instance
app = Flask(__name__)
api = Api(app)

# Sample data storage
videos = [
    {
        'id': 1,
        'title': 'How to Code in Python',
        'views': 1000,
        'likes': 50
    },
    {
        'id': 2,
        'title': 'Flask API Tutorial',
        'views': 2000,
        'likes': 100
    }
]

# Helper function to find video by ID
def find_video(video_id):
    for video in videos:
        if video['id'] == video_id:
            return video
    return None

# Helper function to validate video data
def validate_video_data(data):
    if 'title' not in data or not data['title']:
        abort(400, message='Title is required')
    if 'views' not in data or not isinstance(data['views'], int):
        abort(400, message='Views must be an integer')
    if 'likes' not in data or not isinstance(data['likes'], int):
        abort(400, message='Likes must be an integer')

# Resource for individual videos
class Video(Resource):
    def get(self, video_id):
        video = find_video(video_id)
        if not video:
            abort(404, message='Video not found')
        return video
    
    def put(self, video_id):
        args = parser.parse_args()
        validate_video_data(args)
        
        video = find_video(video_id)
        if not video:
            abort(404, message='Video not found')
            
        video.update(args)
        return video, 200
    
    def delete(self, video_id):
        global videos
        video = find_video(video_id)
        if not video:
            abort(404, message='Video not found')
        
        videos = [v for v in videos if v['id'] != video_id]
        return '', 204

# Resource for all videos
class Videos(Resource):
    def get(self):
        return videos
    
    def post(self):
        args = parser.parse_args()
        validate_video_data(args)
        
        new_id = max([v['id'] for v in videos]) + 1 if videos else 1
        new_video = {
            'id': new_id,
            'title': args['title'],
            'views': args['views'],
            'likes': args['likes']
        }
        videos.append(new_video)
        return new_video, 201

# Parser for request arguments
parser = reqparse.RequestParser()
parser.add_argument('title', type=str, required=True, help='Title of the video')
parser.add_argument('views', type=int, required=True, help='Number of views')
parser.add_argument('likes', type=int, required=True, help='Number of likes')

# Add resources to API with URL routes
api.add_resource(Video, '/video/<int:video_id>')
api.add_resource(Videos, '/videos')

# Health check endpoint
@app.route('/health')
def health_check():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run(debug=True)