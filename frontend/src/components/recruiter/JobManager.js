import React, { useState, useEffect } from 'react';
import {
    Box,
    Typography,
    Button,
    Card,
    CardContent,
    CardActions,
    Grid,
    Chip,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Alert,
    CircularProgress,
    Stepper,
    Step,
    StepLabel,
    Paper,
    IconButton,
    LinearProgress
} from '@mui/material';
import { 
    Add as AddIcon, 
    Edit as EditIcon,
    Upload as UploadIcon,
    Download as DownloadIcon,
    Refresh as RefreshIcon
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { jobAPI } from '../../api';

const JOB_TYPES = ['Contract', 'Full-time', 'C2C', 'W2'];

const JobManager = () => {
    const [jobs, setJobs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [dialogOpen, setDialogOpen] = useState(false);
    const [activeStep, setActiveStep] = useState(0); // 0 = Stage 1 (paste JD), 1 = Stage 2 (edit form)
    const [editingJob, setEditingJob] = useState(null);
    const [jdText, setJdText] = useState('');
    const [classifying, setClassifying] = useState(false);
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        client_name: '',
        experience_required: 0,
        tech_required: [],
        location: '',
        visa_required: '',
        start_date: null,
        job_type: '',
        jd_summary: '',
        additional_notes: '',
        status: 'OPEN'
    });
    const [techInput, setTechInput] = useState(''); // For comma-separated tech input
    const [jdFile, setJdFile] = useState(null);
    const [uploadingFile, setUploadingFile] = useState(false);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });

    useEffect(() => {
        fetchJobs();
    }, []);

    const fetchJobs = async () => {
        try {
            const response = await jobAPI.getAll();
            setJobs(response.data);
        } catch (error) {
            console.error('Error fetching jobs:', error);
            setMessage({ type: 'error', text: 'Failed to load jobs' });
        } finally {
            setLoading(false);
        }
    };

    const handleOpenDialog = (job = null) => {
        if (job) {
            // Editing existing job - go directly to form
            setEditingJob(job);
            setActiveStep(1);
            setFormData({
                title: job.title || '',
                description: job.description || '',
                client_name: job.client_name || '',
                experience_required: job.experience_required || 0,
                tech_required: job.tech_required || [],
                location: job.location || '',
                visa_required: job.visa_required || '',
                start_date: job.start_date ? new Date(job.start_date) : null,
                job_type: job.job_type || '',
                jd_summary: job.jd_summary || '',
                additional_notes: job.additional_notes || '',
                status: job.status || 'OPEN'
            });
            setTechInput(job.tech_required ? job.tech_required.join(', ') : '');
            setJdText('');
        } else {
            // Creating new job - start at Stage 1
            setEditingJob(null);
            setActiveStep(0);
            setJdText('');
            setFormData({
                title: '',
                description: '',
                client_name: '',
                experience_required: 0,
                tech_required: [],
                location: '',
                visa_required: '',
                start_date: null,
                job_type: '',
                jd_summary: '',
                additional_notes: '',
                status: 'OPEN'
            });
            setTechInput('');
            setJdFile(null);
        }
        setMessage({ type: '', text: '' });
        setDialogOpen(true);
    };

    const handleClassifyJD = async () => {
        if (!jdText.trim()) {
            setMessage({ type: 'error', text: 'Please paste job description text' });
            return;
        }

        setClassifying(true);
        setMessage({ type: '', text: '' });

        try {
            const response = await jobAPI.classifyJD(jdText);
            const classified = response.data;

            // Populate form with classified data
            setFormData({
                title: classified.title || '',
                description: classified.description || jdText,
                client_name: classified.client_name || '',
                experience_required: classified.experience_required || 0,
                tech_required: classified.tech_required || [],
                location: classified.location || '',
                visa_required: classified.visa_required || '',
                start_date: classified.start_date ? new Date(classified.start_date) : null,
                job_type: classified.job_type || '',
                jd_summary: classified.jd_summary || '',
                additional_notes: classified.additional_notes || '',
                status: 'OPEN'
            });
            setTechInput(classified.tech_required ? classified.tech_required.join(', ') : '');

            // Move to Stage 2
            setActiveStep(1);
            setMessage({ type: 'success', text: 'JD classified successfully! Please review and edit the fields.' });
        } catch (error) {
            console.error('Error classifying JD:', error);
            const errorMsg = error.response?.data?.detail || 'Failed to classify JD. You can still fill the form manually.';
            setMessage({ type: 'error', text: errorMsg });
            // Still allow manual entry - move to Stage 2
            setFormData(prev => ({ ...prev, description: jdText }));
            setActiveStep(1);
        } finally {
            setClassifying(false);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleTechInputChange = (e) => {
        setTechInput(e.target.value);
        const techArray = e.target.value.split(',').map(t => t.trim()).filter(t => t);
        setFormData(prev => ({ ...prev, tech_required: techArray }));
    };

    const handleDateChange = (date) => {
        setFormData(prev => ({ ...prev, start_date: date }));
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            // Validate file type
            const validTypes = ['.pdf', '.doc', '.docx'];
            const fileExt = '.' + file.name.split('.').pop().toLowerCase();
            if (!validTypes.includes(fileExt)) {
                setMessage({ type: 'error', text: 'Invalid file type. Please upload PDF, DOC, or DOCX files only.' });
                return;
            }
            setJdFile(file);
        }
    };

    const handleSubmit = async () => {
        setSaving(true);
        setMessage({ type: '', text: '' });

        try {
            // Prepare payload
            const payload = {
                ...formData,
                experience_required: Number(formData.experience_required),
                tech_required: formData.tech_required,
                start_date: formData.start_date ? formData.start_date.toISOString() : null,
            };

            let savedJob;
            if (editingJob) {
                // Update existing job
                const response = await jobAPI.update(editingJob.id, payload);
                savedJob = response.data;
            } else {
                // Create new job
                const response = await jobAPI.create(payload);
                savedJob = response.data;
            }

            // Upload file if provided
            if (jdFile && savedJob.id) {
                setUploadingFile(true);
                try {
                    await jobAPI.uploadJDFile(savedJob.id, jdFile);
                } catch (fileError) {
                    console.error('Error uploading file:', fileError);
                    // Don't fail the whole operation if file upload fails
                    setMessage({ type: 'warning', text: 'Job saved but file upload failed. You can upload it later.' });
                } finally {
                    setUploadingFile(false);
                }
            }

            setMessage({ type: 'success', text: `Job ${editingJob ? 'updated' : 'created'} successfully` });
            fetchJobs();
            setTimeout(() => setDialogOpen(false), 1500);
        } catch (error) {
            console.error('Error saving job:', error);
            const errorMsg = error.response?.data?.detail || 'Failed to save job';
            setMessage({ type: 'error', text: errorMsg });
        } finally {
            setSaving(false);
        }
    };

    const handleStartOver = () => {
        setActiveStep(0);
        setJdText('');
        setMessage({ type: '', text: '' });
    };

    if (loading) return <CircularProgress />;

    return (
        <Box sx={{ mt: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h5">Job Descriptions</Typography>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => handleOpenDialog()}
                >
                    Create New JD
                </Button>
            </Box>

            <Grid container spacing={3}>
                {jobs.map((job) => (
                    <Grid item xs={12} md={6} key={job.id}>
                        <Card>
                            <CardContent>
                                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                                    <Typography variant="h6">{job.title}</Typography>
                                    <Chip
                                        label={job.status}
                                        color={job.status === 'OPEN' ? 'success' : 'default'}
                                        size="small"
                                    />
                                </Box>
                                {job.client_name && (
                                    <Typography color="text.secondary" gutterBottom>
                                        Client: {job.client_name}
                                    </Typography>
                                )}
                                <Typography color="text.secondary" gutterBottom>
                                    {job.location || 'Location not specified'} • {job.experience_required}+ Years
                                    {job.job_type && ` • ${job.job_type}`}
                                </Typography>
                                <Box mb={2}>
                                    {job.tech_required && job.tech_required.map((tech) => (
                                        <Chip key={tech} label={tech} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                                    ))}
                                </Box>
                                <Typography variant="body2" color="text.secondary">
                                    {job.jd_summary || job.description?.substring(0, 100)}...
                                </Typography>
                            </CardContent>
                            <CardActions>
                                <Button size="small" startIcon={<EditIcon />} onClick={() => handleOpenDialog(job)}>
                                    Edit
                                </Button>
                                {job.jd_file_url && (
                                    <Button 
                                        size="small" 
                                        startIcon={<DownloadIcon />}
                                        onClick={() => {
                                            // Download file
                                            window.open(`/api/jobs/${job.id}/download-jd-file`, '_blank');
                                        }}
                                    >
                                        Download JD File
                                    </Button>
                                )}
                            </CardActions>
                        </Card>
                    </Grid>
                ))}
            </Grid>

            <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
                <DialogTitle>
                    {editingJob ? 'Edit Job Description' : 'Create New Job Description'}
                </DialogTitle>
                <DialogContent>
                    {!editingJob && (
                        <Stepper activeStep={activeStep} sx={{ mb: 3, mt: 2 }}>
                            <Step>
                                <StepLabel>Paste JD Text</StepLabel>
                            </Step>
                            <Step>
                                <StepLabel>Review & Edit</StepLabel>
                            </Step>
                        </Stepper>
                    )}

                    {message.text && (
                        <Alert severity={message.type} sx={{ mb: 2 }}>
                            {message.text}
                        </Alert>
                    )}

                    {activeStep === 0 && !editingJob && (
                        <Box>
                            <Typography variant="h6" gutterBottom>
                                Step 1: Paste Job Description
                            </Typography>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                Paste the job description text below. Our AI will automatically extract and classify the information.
                            </Typography>
                            <TextField
                                fullWidth
                                multiline
                                rows={12}
                                label="Job Description Text"
                                value={jdText}
                                onChange={(e) => setJdText(e.target.value)}
                                placeholder="Paste the complete job description here..."
                                sx={{ mt: 2 }}
                            />
                            {classifying && (
                                <Box sx={{ mt: 2 }}>
                                    <LinearProgress />
                                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                        Classifying job description...
                                    </Typography>
                                </Box>
                            )}
                        </Box>
                    )}

                    {activeStep === 1 && (
                        <Box>
                            {!editingJob && (
                                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                                    <Typography variant="h6">
                                        Step 2: Review & Edit Classified Fields
                                    </Typography>
                                    <Button
                                        size="small"
                                        startIcon={<RefreshIcon />}
                                        onClick={handleStartOver}
                                    >
                                        Start Over
                                    </Button>
                                </Box>
                            )}
                            <Grid container spacing={2}>
                                <Grid item xs={12} sm={8}>
                                    <TextField
                                        fullWidth
                                        label="Job Title *"
                                        name="title"
                                        value={formData.title}
                                        onChange={handleChange}
                                        required
                                    />
                                </Grid>
                                <Grid item xs={12} sm={4}>
                                    <FormControl fullWidth>
                                        <InputLabel>Status</InputLabel>
                                        <Select
                                            name="status"
                                            value={formData.status}
                                            label="Status"
                                            onChange={handleChange}
                                        >
                                            <MenuItem value="OPEN">OPEN</MenuItem>
                                            <MenuItem value="CLOSED">CLOSED</MenuItem>
                                        </Select>
                                    </FormControl>
                                </Grid>
                                <Grid item xs={12} sm={6}>
                                    <TextField
                                        fullWidth
                                        label="Client/Company Name"
                                        name="client_name"
                                        value={formData.client_name}
                                        onChange={handleChange}
                                    />
                                </Grid>
                                <Grid item xs={12} sm={6}>
                                    <FormControl fullWidth>
                                        <InputLabel>Job Type</InputLabel>
                                        <Select
                                            name="job_type"
                                            value={formData.job_type}
                                            label="Job Type"
                                            onChange={handleChange}
                                        >
                                            <MenuItem value="">None</MenuItem>
                                            {JOB_TYPES.map(type => (
                                                <MenuItem key={type} value={type}>{type}</MenuItem>
                                            ))}
                                        </Select>
                                    </FormControl>
                                </Grid>
                                <Grid item xs={12} sm={6}>
                                    <TextField
                                        fullWidth
                                        label="Required Experience (Years)"
                                        name="experience_required"
                                        type="number"
                                        value={formData.experience_required}
                                        onChange={handleChange}
                                        inputProps={{ min: 0, step: 0.5 }}
                                    />
                                </Grid>
                                <Grid item xs={12} sm={6}>
                                    <LocalizationProvider dateAdapter={AdapterDateFns}>
                                        <DatePicker
                                            label="Start Date/Availability"
                                            value={formData.start_date}
                                            onChange={handleDateChange}
                                            slotProps={{
                                                textField: {
                                                    fullWidth: true
                                                }
                                            }}
                                        />
                                    </LocalizationProvider>
                                </Grid>
                                <Grid item xs={12} sm={6}>
                                    <TextField
                                        fullWidth
                                        label="Location"
                                        name="location"
                                        value={formData.location}
                                        onChange={handleChange}
                                    />
                                </Grid>
                                <Grid item xs={12} sm={6}>
                                    <TextField
                                        fullWidth
                                        label="Visa Requirements"
                                        name="visa_required"
                                        value={formData.visa_required}
                                        onChange={handleChange}
                                    />
                                </Grid>
                                <Grid item xs={12}>
                                    <TextField
                                        fullWidth
                                        label="Required Tech Stack/Skills (comma separated)"
                                        value={techInput}
                                        onChange={handleTechInputChange}
                                        placeholder="React, Python, AWS, Docker"
                                        helperText="Enter technologies separated by commas"
                                    />
                                </Grid>
                                <Grid item xs={12}>
                                    <TextField
                                        fullWidth
                                        label="JD Summary/Description"
                                        name="jd_summary"
                                        multiline
                                        rows={3}
                                        value={formData.jd_summary}
                                        onChange={handleChange}
                                        placeholder="Brief summary of the job description"
                                    />
                                </Grid>
                                <Grid item xs={12}>
                                    <TextField
                                        fullWidth
                                        label="Full Job Description *"
                                        name="description"
                                        multiline
                                        rows={6}
                                        value={formData.description}
                                        onChange={handleChange}
                                        required
                                    />
                                </Grid>
                                <Grid item xs={12}>
                                    <TextField
                                        fullWidth
                                        label="Additional Notes"
                                        name="additional_notes"
                                        multiline
                                        rows={3}
                                        value={formData.additional_notes}
                                        onChange={handleChange}
                                        placeholder="Any additional notes or requirements"
                                    />
                                </Grid>
                                <Grid item xs={12}>
                                    <Box>
                                        <input
                                            accept=".pdf,.doc,.docx"
                                            style={{ display: 'none' }}
                                            id="jd-file-upload"
                                            type="file"
                                            onChange={handleFileChange}
                                        />
                                        <label htmlFor="jd-file-upload">
                                            <Button
                                                variant="outlined"
                                                component="span"
                                                startIcon={<UploadIcon />}
                                                fullWidth
                                            >
                                                {jdFile ? jdFile.name : 'Upload JD File (PDF/DOC) - Optional'}
                                            </Button>
                                        </label>
                                        {jdFile && (
                                            <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                                                Selected: {jdFile.name}
                                            </Typography>
                                        )}
                                    </Box>
                                </Grid>
                            </Grid>
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
                    {activeStep === 0 && !editingJob && (
                        <Button
                            onClick={handleClassifyJD}
                            variant="contained"
                            disabled={classifying || !jdText.trim()}
                            startIcon={classifying ? <CircularProgress size={16} /> : null}
                        >
                            {classifying ? 'Classifying...' : 'Classify with AI'}
                        </Button>
                    )}
                    {activeStep === 1 && (
                        <Button
                            onClick={handleSubmit}
                            variant="contained"
                            disabled={saving || uploadingFile || !formData.title || !formData.description}
                        >
                            {saving || uploadingFile ? 'Saving...' : editingJob ? 'Update Job' : 'Save Job'}
                        </Button>
                    )}
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default JobManager;
