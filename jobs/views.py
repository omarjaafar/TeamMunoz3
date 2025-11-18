from django.shortcuts import render, redirect, get_object_or_404
from .models import Job
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from applications.models import Application
from django.urls import reverse
from accounts.models import Profile
import re
# Create your views here.

@login_required
def index(request):
    #first we go to the jobs table in the database, then give me the rows that are 
    # created by the currently logged in user
    jobs = Job.objects.filter(posted_by=request.user)
    template_data = {
        'title': 'Post a Job',
        'jobs' : jobs
    }
    return render(request, 'jobs/index.html', {'template_data' : template_data})

# pk is a primary key that identifies a specific Job row in the database
# when pk is None, we are creating a new job
# when pk has a value, we edit that existing job
@login_required
def job_form(request, pk=None):
    job = None
    # this checks if a pk for the job currently exists - if it doesn't return 404 error
    # commenting this out would no longer show the data for each of the jobs posted!
    if pk is not None:
        job = get_object_or_404(Job, pk=pk, posted_by=request.user)

    if request.method == 'POST':
        data = request.POST
        fields = {
            'title': (data.get('title') or '').strip(),
            'company': (data.get('company') or '').strip(),
            'location': (data.get('location') or '').strip(),
            'job_type': data.get('job_type') or 'FT',
            'salary': data.get('salary') or None,
            'description': (data.get('description') or '').strip(),
        }

        if job is None:
            #capture the instance, then redirect using its pk - define the fields dict here 
            job = Job.objects.create(posted_by=request.user, **fields)
            return redirect(reverse('jobs.index'), pk=job.pk)

        # update the existing instance, then redirect
        # the for-loop below iterates through the (key, value) pairs in the 'fields' dict
        # for each field name (k) and submitted value (v), we set that attribute on the
        # existing job instance, like setattr(job, 'title', 'New Title')
        for k, v in fields.items():
            setattr(job, k, v)
            job.save()
        return redirect('jobs.index')  

    template_data = {'title': 'Add Job' if job is None else f'Edit: {job.title}', 'job': job}
    return render(request, 'jobs/form.html', {'template_data': template_data})

@login_required
@require_POST
def delete(request, pk):
    # delete only if it belongs to the current user
    deleted_count, _ = Job.objects.filter(pk=pk, posted_by=request.user).delete()
    if deleted_count == 0:
        messages.error(request, "That job wasn't found (or it isn't yours).")
    else:
        messages.success(request, "Job deleted.")
    return redirect('jobs.index')

@login_required
@require_POST
def apply_to_job(request, pk):
    job = get_object_or_404(Job, pk=pk)

    # Prevent recruiters from applying to jobs
    if hasattr(request.user, "profile") and request.user.profile.role != "JOB_SEEKER":
        messages.error(request, "Only job seekers can apply to jobs.")
        return redirect('seeker.apply')

    note = (request.POST.get("note") or "").strip()
    application, created = Application.objects.get_or_create(
        job=job,
        applicant=request.user,
        defaults={"notes": note}
    )

    if created:
        messages.success(request, f"Successfully applied to {job.title}.")
    else:
        # If they re-apply with a new note, update (your choice)
        if note:
            application.notes = note
            application.save(update_fields=["notes"])
            messages.success(request, "Your note was updated for this application.")
        else:
            messages.info(request, "You already applied to this job.")


    return redirect('seeker.apply')

@login_required
def job_candidate_recommendations(request, pk):
    """
    View to show candidate recommendations for a specific job posting.
    Only accessible by the recruiter who posted the job.
    Enhanced with better skill matching algorithm.
    """
    from home.views import is_recruiter
    
    # Verify user is a recruiter
    if not is_recruiter(request.user):
        messages.error(request, "Only recruiters can view candidate recommendations.")
        return redirect('jobs.index')
    
    # Get the job and verify it belongs to the current recruiter
    job = get_object_or_404(Job, pk=pk)
    if job.posted_by != request.user:
        messages.error(request, "You can only view recommendations for your own job postings.")
        return redirect('jobs.index')
    
    # Get all job seekers (candidates)
    candidates = Profile.objects.filter(role=Profile.JOB_SEEKER).select_related('user')
    
    # Get IDs of candidates who already applied to this job
    existing_applicants = Application.objects.filter(job=job).values_list('applicant_id', flat=True)
    candidates = candidates.exclude(user_id__in=existing_applicants)
    
    # Common stop words to filter out (non-technical common words)
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must',
        'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both',
        'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 'just', 'about', 'into', 'through', 'during',
        'including', 'against', 'among', 'throughout', 'despite', 'towards', 'upon', 'concerning'
    }
    
    # Common technical terms that should be weighted higher
    technical_indicators = {
        'api', 'aws', 'azure', 'ci/cd', 'css', 'docker', 'git', 'github', 'html', 'http',
        'javascript', 'json', 'kubernetes', 'linux', 'ml', 'mysql', 'nosql', 'postgresql',
        'python', 'react', 'rest', 'sql', 'typescript', 'ui/ux', 'xml', 'agile', 'scrum',
        'devops', 'microservices', 'graphql', 'mongodb', 'redis', 'elasticsearch', 'kafka'
    }
    
    def normalize_skill(skill_text):
        """Normalize a skill: lowercase, remove special chars, handle variations"""
        if not skill_text:
            return ''
        # Lowercase and strip
        normalized = skill_text.lower().strip()
        # Remove common suffixes/variations (e.g., .js, .net, etc.)
        normalized = re.sub(r'\.(js|net|py|ts|java)$', r'', normalized)
        # Remove special characters except hyphens (for things like "ci/cd")
        normalized = re.sub(r'[^\w\s/-]', '', normalized)
        # Normalize spacing
        normalized = ' '.join(normalized.split())
        return normalized
    
    def extract_skills(text):
        """Extract skill-like tokens from text"""
        if not text:
            return set()
        text_lower = text.lower()
        
        # Split by common delimiters
        tokens = re.split(r'[,;\n\r|/\s()]+', text_lower)
        skills = set()
        
        for token in tokens:
            token = token.strip()
            # Filter: must be 2+ chars, not a stop word, not purely numeric
            if (len(token) >= 2 and 
                token not in stop_words and 
                not token.isdigit() and
                not re.match(r'^\d+$', token)):  # Not pure numbers
                normalized = normalize_skill(token)
                if normalized and len(normalized) >= 2:
                    skills.add(normalized)
        
        return skills
    
    def whole_word_match(needle, haystack):
        """Check if needle appears as a whole word in haystack (case-insensitive)"""
        if not needle or not haystack:
            return False
        # Use word boundaries for whole-word matching
        pattern = r'\b' + re.escape(needle.lower()) + r'\b'
        return bool(re.search(pattern, haystack.lower()))
    
    # Extract skills from job posting (title and description are most important)
    job_title_text = (job.title or '').lower()
    job_desc_text = (job.description or '').lower()
    job_full_text = ' '.join([
        job_title_text,
        job_desc_text,
        job.company or '',
        job.location or ''
    ]).lower()
    
    # Extract skills from job
    job_skills = extract_skills(job_title_text + ' ' + job_desc_text)
    
    # Build recommendation scores for each candidate
    recommendations = []
    
    for candidate in candidates:
        score = 0
        matched_keywords = []
        matched_skills = []
        
        # Extract candidate skills
        candidate_skills_raw = candidate.skills or ''
        candidate_skills_set = extract_skills(candidate_skills_raw)
        
        # Combine candidate profile fields for matching
        candidate_text = ' '.join([
            candidate.headline or '',
            candidate_skills_raw,
            candidate.experience or '',
            candidate.education or '',
            candidate.projects or ''
        ]).lower()
        
        # Primary matching: Direct skill-to-skill matching (highest weight)
        for job_skill in job_skills:
            for cand_skill in candidate_skills_set:
                # Exact match
                if job_skill == cand_skill:
                    score += 5  # High weight for exact skill match
                    if job_skill not in matched_skills:
                        matched_skills.append(job_skill)
                        matched_keywords.append(job_skill)
                # One contains the other (e.g., "python" matches "python3", "react" matches "react.js")
                elif job_skill in cand_skill or cand_skill in job_skill:
                    # Only if significant overlap (avoid false positives)
                    min_len = min(len(job_skill), len(cand_skill))
                    if min_len >= 3:  # At least 3 chars to avoid "go" matching "ago"
                        score += 4
                        if job_skill not in matched_skills:
                            matched_skills.append(job_skill)
                            matched_keywords.append(job_skill)
        
        # Secondary matching: Check if job skills appear in candidate's full profile text
        for job_skill in job_skills:
            if job_skill not in matched_skills:
                # Use whole-word matching to avoid false positives
                if whole_word_match(job_skill, candidate_text):
                    # Check if it's a technical term for higher weight
                    if job_skill in technical_indicators or len(job_skill) >= 4:
                        score += 3  # Technical skills get higher weight
                    else:
                        score += 2
                    matched_keywords.append(job_skill)
        
        # Tertiary matching: Check if candidate skills appear in job text (as whole words)
        for cand_skill in candidate_skills_set:
            if cand_skill not in matched_skills:
                if whole_word_match(cand_skill, job_full_text):
                    if cand_skill in technical_indicators or len(cand_skill) >= 4:
                        score += 3
                    else:
                        score += 2
                    if cand_skill not in matched_keywords:
                        matched_keywords.append(cand_skill)
        
        # Location matching bonus
        if job.location and candidate.location:
            job_loc_lower = job.location.lower()
            cand_loc_lower = candidate.location.lower()
            # Exact match or partial match (e.g., "New York" matches "New York City")
            if job_loc_lower in cand_loc_lower or cand_loc_lower in job_loc_lower:
                score += 2
            # Check for same city/state (simple heuristic)
            elif any(part in cand_loc_lower for part in job_loc_lower.split() if len(part) > 3):
                score += 1
        
        # Only include candidates with some match
        if score > 0:
            # Combine matched skills and other keywords, prioritizing skills
            all_keywords = list(set(matched_keywords))  # Remove duplicates
            # Sort: matched skills first, then by length (longer = more specific)
            all_keywords.sort(key=lambda x: (
                x not in matched_skills,  # Skills first
                -len(x),  # Longer keywords first
                x  # Alphabetical as tiebreaker
            ))
            
            recommendations.append({
                'candidate': candidate,
                'score': score,
                'matched_keywords': all_keywords[:12],  # Limit displayed keywords
                'matched_skills': matched_skills[:8],  # Top matched skills
                'total_matches': len(all_keywords)  # Total count for template
            })
    
    # Sort by score (descending) and take top 20
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    recommendations = recommendations[:20]
    
    template_data = {
        'title': f'Candidate Recommendations for {job.title}',
        'job': job,
        'recommendations': recommendations,
    }
    return render(request, 'jobs/candidate_recommendations.html', {'template_data': template_data})