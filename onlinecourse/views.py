from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Course, Question, Choice, Submission


@login_required
def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)

    if request.method != "POST":
        return redirect("onlinecourse:course_details", course_id=course.id)

    submission = Submission.objects.create(
        user=request.user,
        course=course,
    )

    selected_ids = request.POST.getlist("choices")

    valid_choices = Choice.objects.filter(
        pk__in=selected_ids,
        question__course=course,
    )

    submission.choices.set(valid_choices)

    return redirect(
        "onlinecourse:show_exam_result",
        course_id=course.id,
        submission_id=submission.id,
    )


@login_required
def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, pk=course_id)

    submission = get_object_or_404(
        Submission,
        pk=submission_id,
        course=course,
        user=request.user,
    )

    questions = Question.objects.filter(course=course).prefetch_related(
        "choices"
    )

    score = 0
    exam_results = []

    for question in questions:
        correct_choices = set(
            question.choices.filter(is_correct=True).values_list(
                "id", flat=True
            )
        )
        selected_choices = set(
            submission.choices.filter(question=question).values_list(
                "id", flat=True
            )
        )

        is_correct = (
            bool(correct_choices)
            and selected_choices == correct_choices
        )

        if is_correct:
            score += question.grade

        exam_results.append({
            "question": question,
            "choices": question.choices.all(),
            "selected_choices": selected_choices,
            "is_correct": is_correct,
        })

    return render(
        request,
        "onlinecourse/exam_result_bootstrap.html",
        {
            "course": course,
            "submission": submission,
            "score": score,
            "exam_results": exam_results,
        },
    )