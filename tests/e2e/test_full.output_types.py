from typing import Optional, List, Union

from typing_extensions import TypedDict


class ThumbnailsType(TypedDict, total=False):
    xs: str
    sm: str
    md: str
    lg: str
    xl: str


class HostsItem0Type(TypedDict, total=False):
    name: str
    id: str


class AuthorsItem0Type(TypedDict, total=False):
    name: str
    id: str


class PublicationDateType(TypedDict, total=False):
    year: int
    month: int
    day: int
    century: int
    ad_bc: str


class SourceType(TypedDict, total=False):
    user_id: str
    path: str
    thumbnails: ThumbnailsType
    title: str
    description: str
    hosts: List[HostsItem0Type]
    authors: List[AuthorsItem0Type]
    publication_date: PublicationDateType
    content_type: str


class MarkdownType(TypedDict, total=False):
    text: str


class CaptionsType(TypedDict, total=False):
    path: str
    language: str
    format: str
    encoding: str
    is_auto_generated: bool


class VideoType(TypedDict, total=False):
    path: str
    duration: int
    resolution: str
    bitrate: int
    frame_rate: int
    codec: str
    format: str
    captions: CaptionsType


class AudioType(TypedDict, total=False):
    path: str
    duration: int
    bitrate: int
    sample_rate: int
    channels: int
    format: str
    language: str


class EmbeddingsType(TypedDict, total=False):
    first_sentence: List[float]
    paragraph: List[float]
    last_sentence: List[float]


class ParagraphsItem0Type(TypedDict, total=False):
    uuid: str
    antecedent_sim: float
    heading: str
    text: str
    timespan: List[Union[float, int]]
    line_numbers: List[int]
    page: int
    embeddings: EmbeddingsType


class SubjectType(TypedDict, total=False):
    type: str
    id: str
    sources: List[str]


class TriplesItem0Type(TypedDict, total=False):
    subject: SubjectType
    predicate: SubjectType
    object: SubjectType


class RdfItem0Type(TypedDict, total=False):
    triples: List[TriplesItem0Type]


class RootType(TypedDict, total=False):
    manual_input: bool
    source: SourceType
    markdown: MarkdownType
    video: VideoType
    audio: AudioType
    paragraphs: List[ParagraphsItem0Type]
    rdf: List[RdfItem0Type]

OptionalRoot = Optional[RootType]