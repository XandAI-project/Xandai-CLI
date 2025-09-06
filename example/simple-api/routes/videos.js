const express = require('express');
const router = express.Router();
const Video = require('../models/video');
const { validateVideoCreation, validateVideoUpdate } = require('../middleware/validation');

// GET /api/videos - Retrieve all videos
router.get('/', (req, res) => {
  try {
    const videos = Video.getAllVideos();
    return res.status(200).json(videos);
  } catch (error) {
    return res.status(500).json({ error: 'Failed to retrieve videos' });
  }
});

// GET /api/video/:id - Retrieve a specific video by ID
router.get('/:id', (req, res) => {
  try {
    const id = parseInt(req.params.id);
    if (isNaN(id)) {
      return res.status(400).json({ error: 'Invalid video ID' });
    }

    const video = Video.getVideoById(id);
    if (!video) {
      return res.status(404).json({ error: 'Video not found' });
    }

    return res.status(200).json(video);
  } catch (error) {
    return res.status(500).json({ error: 'Failed to retrieve video' });
  }
});

// POST /api/videos - Create a new video
router.post('/', validateVideoCreation, (req, res) => {
  try {
    const { title, views, likes } = req.body;
    const newVideo = Video.createVideo({ title, views, likes });
    return res.status(201).json(newVideo);
  } catch (error) {
    return res.status(500).json({ error: 'Failed to create video' });
  }
});

// PUT /api/video/:id - Update an existing video by ID
router.put('/:id', validateVideoUpdate, (req, res) => {
  try {
    const id = parseInt(req.params.id);
    if (isNaN(id)) {
      return res.status(400).json({ error: 'Invalid video ID' });
    }

    const { title, views, likes } = req.body;
    const updatedVideo = Video.updateVideo(id, { title, views, likes });

    if (!updatedVideo) {
      return res.status(404).json({ error: 'Video not found' });
    }

    return res.status(200).json(updatedVideo);
  } catch (error) {
    return res.status(500).json({ error: 'Failed to update video' });
  }
});

// DELETE /api/video/:id - Delete a specific video by ID
router.delete('/:id', (req, res) => {
  try {
    const id = parseInt(req.params.id);
    if (isNaN(id)) {
      return res.status(400).json({ error: 'Invalid video ID' });
    }

    const deleted = Video.deleteVideo(id);
    if (!deleted) {
      return res.status(404).json({ error: 'Video not found' });
    }

    return res.status(204).send();
  } catch (error) {
    return res.status(500).json({ error: 'Failed to delete video' });
  }
});

module.exports = router;
