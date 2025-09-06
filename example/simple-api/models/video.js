const mongoose = require('mongoose');

/**
 * Video schema definition
 * @typedef {Object} Video
 * @property {string} title - The video title
 * @property {number} views - Number of views
 * @property {number} likes - Number of likes
 */

const videoSchema = new mongoose.Schema({
  title: {
    type: String,
    required: [true, 'Title is required'],
    trim: true,
    maxlength: [200, 'Title cannot exceed 200 characters']
  },
  views: {
    type: Number,
    required: [true, 'Views count is required'],
    min: [0, 'Views count cannot be negative']
  },
  likes: {
    type: Number,
    required: [true, 'Likes count is required'],
    min: [0, 'Likes count cannot be negative']
  }
}, {
  timestamps: true
});

/**
 * Validate video data before saving
 * @param {Object} videoData - The video data to validate
 * @returns {Object} Validation result with errors and isValid flag
 */
videoSchema.statics.validateVideoData = function(videoData) {
  const errors = [];

  if (!videoData.title || videoData.title.trim() === '') {
    errors.push('Title is required');
  }

  if (typeof videoData.views !== 'number' || videoData.views < 0) {
    errors.push('Views must be a non-negative number');
  }

  if (typeof videoData.likes !== 'number' || videoData.likes < 0) {
    errors.push('Likes must be a non-negative number');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
};

/**
 * Sanitize input data to prevent injection attacks
 * @param {Object} inputData - The raw input data
 * @returns {Object} Sanitized video data
 */
videoSchema.statics.sanitizeInput = function(inputData) {
  return {
    title: inputData.title ? inputData.title.trim() : '',
    views: parseInt(inputData.views) || 0,
    likes: parseInt(inputData.likes) || 0
  };
};

/**
 * Get video summary information
 * @returns {Object} Summary of video information
 */
videoSchema.methods.getSummary = function() {
  return {
    id: this._id,
    title: this.title,
    views: this.views,
    likes: this.likes
  };
};

// Create and export the Video model
const Video = mongoose.model('Video', videoSchema);

module.exports = Video;
