import sgqlc.types
import sgqlc.operation
import schema

_schema = schema
_schema_root = _schema.schema

__all__ = ('Operations',)


def mutation_sync_upstream():
    _op = sgqlc.operation.Operation(_schema_root.mutation_type, name='SyncUpstream', variables=dict(refId=sgqlc.types.Arg(sgqlc.types.non_null(_schema.ID)), oid=sgqlc.types.Arg(sgqlc.types.non_null(_schema.GitObjectID))))
    _op.update_ref(input={'refId': sgqlc.types.Variable('refId'), 'oid': sgqlc.types.Variable('oid')})
    return _op


def mutation_create_branch():
    _op = sgqlc.operation.Operation(_schema_root.mutation_type, name='CreateBranch', variables=dict(name=sgqlc.types.Arg(sgqlc.types.non_null(_schema.String)), baseRef=sgqlc.types.Arg(sgqlc.types.non_null(_schema.GitObjectID)), repoId=sgqlc.types.Arg(sgqlc.types.non_null(_schema.ID))))
    _op_create_ref = _op.create_ref(input={'name': sgqlc.types.Variable('name'), 'oid': sgqlc.types.Variable('baseRef'), 'repositoryId': sgqlc.types.Variable('repoId')})
    _op_create_ref_ref = _op_create_ref.ref()
    _op_create_ref_ref.id()
    return _op


def mutation_create_commit():
    _op = sgqlc.operation.Operation(_schema_root.mutation_type, name='CreateCommit', variables=dict(repoName=sgqlc.types.Arg(sgqlc.types.non_null(_schema.String)), branchName=sgqlc.types.Arg(sgqlc.types.non_null(_schema.String)), head=sgqlc.types.Arg(sgqlc.types.non_null(_schema.GitObjectID)), commitMsg=sgqlc.types.Arg(sgqlc.types.non_null(_schema.String)), filePath=sgqlc.types.Arg(sgqlc.types.non_null(_schema.String)), contents=sgqlc.types.Arg(sgqlc.types.non_null(_schema.Base64String))))
    _op.create_commit_on_branch(input={'branch': {'repositoryNameWithOwner': sgqlc.types.Variable('repoName'), 'branchName': sgqlc.types.Variable('branchName')}, 'expectedHeadOid': sgqlc.types.Variable('head'), 'message': {'headline': sgqlc.types.Variable('commitMsg')}, 'fileChanges': {'additions': ({'path': sgqlc.types.Variable('filePath'), 'contents': sgqlc.types.Variable('contents')},)}})
    return _op


def mutation_create_pr():
    _op = sgqlc.operation.Operation(_schema_root.mutation_type, name='CreatePR', variables=dict(title=sgqlc.types.Arg(sgqlc.types.non_null(_schema.String)), repoId=sgqlc.types.Arg(sgqlc.types.non_null(_schema.ID)), headRef=sgqlc.types.Arg(sgqlc.types.non_null(_schema.String)), baseRef=sgqlc.types.Arg(sgqlc.types.non_null(_schema.String)), body=sgqlc.types.Arg(sgqlc.types.non_null(_schema.String))))
    _op_create_pull_request = _op.create_pull_request(input={'title': sgqlc.types.Variable('title'), 'repositoryId': sgqlc.types.Variable('repoId'), 'headRefName': sgqlc.types.Variable('headRef'), 'baseRefName': sgqlc.types.Variable('baseRef'), 'body': sgqlc.types.Variable('body')})
    _op_create_pull_request_pull_request = _op_create_pull_request.pull_request()
    _op_create_pull_request_pull_request.id()
    _op_create_pull_request_pull_request.url()
    return _op


class Mutation:
    create_branch = mutation_create_branch()
    create_commit = mutation_create_commit()
    create_pr = mutation_create_pr()
    sync_upstream = mutation_sync_upstream()


def query_get_refs():
    _op = sgqlc.operation.Operation(_schema_root.query_type, name='GetRefs', variables=dict(owner=sgqlc.types.Arg(sgqlc.types.non_null(_schema.String))))
    _op_repository = _op.repository(owner=sgqlc.types.Variable('owner'), name='this-week-in-neovim-contents')
    _op_repository.id()
    _op_repository_refs = _op_repository.refs(ref_prefix='refs/heads/', last=3)
    _op_repository_refs_edges = _op_repository_refs.edges()
    _op_repository_refs_edges_node = _op_repository_refs_edges.node()
    _op_repository_refs_edges_node.id()
    _op_repository_refs_edges_node.name()
    _op_repository_refs_edges_node_target = _op_repository_refs_edges_node.target()
    _op_repository_refs_edges_node_target.oid()
    return _op


def query_get_first_pr():
    _op = sgqlc.operation.Operation(_schema_root.query_type, name='GetFirstPR')
    _op_repository = _op.repository(owner='phaazon', name='this-week-in-neovim-contents')
    _op_repository_pull_requests = _op_repository.pull_requests(first=1, states=('OPEN',))
    _op_repository_pull_requests_edges = _op_repository_pull_requests.edges()
    _op_repository_pull_requests_edges.cursor()
    _op_repository_pull_requests_edges_node = _op_repository_pull_requests_edges.node()
    _op_repository_pull_requests_edges_node.id()
    _op_repository_pull_requests_edges_node.title()
    _op_repository_pull_requests_edges_node_head_ref = _op_repository_pull_requests_edges_node.head_ref()
    _op_repository_pull_requests_edges_node_head_ref.name()
    _op_repository_pull_requests_edges_node_head_ref_target = _op_repository_pull_requests_edges_node_head_ref.target()
    _op_repository_pull_requests_edges_node_head_ref_target.oid()
    return _op


def query_get_all_prs():
    _op = sgqlc.operation.Operation(_schema_root.query_type, name='GetAllPRs', variables=dict(cursor=sgqlc.types.Arg(sgqlc.types.non_null(_schema.String))))
    _op_repository = _op.repository(owner='phaazon', name='this-week-in-neovim-contents')
    _op_repository_pull_requests = _op_repository.pull_requests(after=sgqlc.types.Variable('cursor'), first=40)
    _op_repository_pull_requests_edges = _op_repository_pull_requests.edges()
    _op_repository_pull_requests_edges_node = _op_repository_pull_requests_edges.node()
    _op_repository_pull_requests_edges_node_files = _op_repository_pull_requests_edges_node.files(first=5)
    _op_repository_pull_requests_edges_node_files_edges = _op_repository_pull_requests_edges_node_files.edges()
    _op_repository_pull_requests_edges_node_files_edges_node = _op_repository_pull_requests_edges_node_files_edges.node()
    _op_repository_pull_requests_edges_node_files_edges_node.path()
    return _op


class Query:
    get_all_prs = query_get_all_prs()
    get_first_pr = query_get_first_pr()
    get_refs = query_get_refs()


class Operations:
    mutation = Mutation
    query = Query
