from typing import List, Optional, Union

from typing_extensions import TypedDict


class ThumbnailsType(TypedDict):
    xs: Optional[str]
    sm: Optional[str]
    md: Optional[str]
    lg: Optional[str]
    xl: Optional[str]


class HostsItem0Type(TypedDict):
    name: Optional[str]
    id: Optional[str]


class AuthorsItem0Type(TypedDict):
    name: Optional[str]
    id: Optional[str]


class PublicationDateType(TypedDict):
    year: Optional[int]
    month: Optional[int]
    day: Optional[int]
    century: Optional[int]
    ad_bc: Optional[str]


class SourceType(TypedDict):
    user_id: Optional[str]
    path: Optional[str]
    thumbnails: Optional[ThumbnailsType]
    title: Optional[str]
    description: Optional[str]
    hosts: Optional[List[HostsItem0Type]]
    authors: Optional[List[AuthorsItem0Type]]
    publication_date: Optional[PublicationDateType]
    content_type: Optional[str]


class MarkdownType(TypedDict):
    text: Optional[str]


class CaptionsType(TypedDict):
    path: Optional[str]
    language: Optional[str]
    format: Optional[str]
    encoding: Optional[str]
    is_auto_generated: Optional[bool]


class VideoType(TypedDict):
    path: Optional[str]
    duration: Optional[int]
    resolution: Optional[str]
    bitrate: Optional[int]
    frame_rate: Optional[int]
    codec: Optional[str]
    format: Optional[str]
    captions: Optional[CaptionsType]


class AudioType(TypedDict):
    path: Optional[str]
    duration: Optional[int]
    bitrate: Optional[int]
    sample_rate: Optional[int]
    channels: Optional[int]
    format: Optional[str]
    language: Optional[str]


class EmbeddingsType(TypedDict):
    first_sentence: Optional[List[float]]
    paragraph: Optional[List[float]]
    last_sentence: Optional[List[float]]


class ParagraphsItem0Type(TypedDict):
    uuid: Optional[str]
    antecedent_sim: Optional[float]
    heading: Optional[str]
    text: Optional[str]
    timespan: Optional[List[Union[float, int]]]
    line_numbers: Optional[List[int]]
    page: Optional[int]
    embeddings: Optional[EmbeddingsType]


class SubjectType(TypedDict):
    type: Optional[str]
    id: Optional[str]
    sources: Optional[List[str]]


class TriplesItem0Type(TypedDict):
    subject: Optional[SubjectType]
    predicate: Optional[SubjectType]
    object: Optional[SubjectType]


class RdfItem0Type(TypedDict):
    triples: Optional[List[TriplesItem0Type]]


class RootType(TypedDict):
    manual_input: Optional[bool]
    source: Optional[SourceType]
    markdown: Optional[MarkdownType]
    video: Optional[VideoType]
    audio: Optional[AudioType]
    paragraphs: Optional[List[ParagraphsItem0Type]]
    rdf: Optional[List[RdfItem0Type]]