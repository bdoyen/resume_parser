from pydantic import BaseModel


class Experience(BaseModel):
    city: str = ""
    title: str = ""
    country: str = ""
    employer: str = ""
    end_date: str = ""
    start_date: str = ""
    description: str = ""
    country_code: str = ""
    custom_sections: list = []


class ExperienceData(BaseModel):
    experience: list[Experience] = []


class SkillsData(BaseModel):
    skills: list[str] = []


class Education(BaseModel):
    city: str = ""
    school: str = ""
    country: str = ""
    end_date: str = ""
    start_date: str = ""
    degree_name: str = ""
    description: str = ""
    country_code: str = ""
    degree_major: str = ""
    custom_sections: list = []


class EducationData(BaseModel):
    education: list[Education] = []


class ContactDetail(BaseModel):
    value: str = ""
    type: str = None


class ContactData(BaseModel):
    email: list[ContactDetail] = []
    phone: list[ContactDetail] = []
    address: list = []
    website: list = []


class SummaryData(BaseModel):
    benefits: str = ""
    objective: str = ""
    description: str = ""
    notice_period: str = ""
    current_salary: str = ""


class PersonalData(BaseModel):
    gender: str = ""
    full_name: str = ""
    birthplace: str = ""
    first_name: str = ""
    family_name: str = ""
    middle_name: str = ""
    nationality: list[str] = []
    picture_url: str = ""
    date_of_birth: str = ""
    marital_status: str = ""
    picture_extension: str = ""


class Language(BaseModel):
    code: str = ""
    name: str = ""
    description: str = ""


class LanguagesData(BaseModel):
    languages: list[Language] = []


class AchievementsData(BaseModel):
    achievements: dict = {}


class CertificationsData(BaseModel):
    achievements: dict = {}


class QualificationsData(BaseModel):
    achievements: dict = {}


class MetaData(BaseModel):
    job_pk: int = 0
    remark: str = ""
    status: str = "unsucceeded"
    resume_pk: str = 0
    candidate_pk: int = 0
    language_code: str = "en"
    language_confidence: float = 1.0


class ResumeParsingResponse(BaseModel):
    skills: SkillsData = []
    contact: ContactData = {}
    summary: SummaryData = {}
    metadata: MetaData = {}
    personal: PersonalData = {}
    education: EducationData = []
    experience: ExperienceData = []
    languages: LanguagesData = []
    achievements: AchievementsData = {}
    certifications: CertificationsData = {}
    qualifications: QualificationsData = {}
