from alternia.core.models import (
    StudentClass,
    StudentQuestion,
)


def main():
    question = StudentQuestion(
        student_id="student_001",
        student_class=StudentClass.TEN,
        question="Explique-moi les équations du premier degré.",
    )

    print("=== AlternIA ===")
    print(f"Élève : {question.student_id}")
    print(f"Classe : {question.student_class.value}")
    print(f"Question : {question.question}")


if __name__ == "__main__":
    main()