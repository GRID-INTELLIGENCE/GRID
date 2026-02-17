# Cascade Chat Conversation

  Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

[{
	"resource": "/e:/grid/application/mothership/main.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"(request: Request, exc: MothershipError) -> CoroutineType[Any, Any, JSONResponse]\" cannot be assigned to parameter \"handler\" of type \"ExceptionHandler\" in function \"add_exception_handler\"\n  Type \"(request: Request, exc: MothershipError) -> CoroutineType[Any, Any, JSONResponse]\" is not assignable to type \"ExceptionHandler\"\n    Type \"(request: Request, exc: MothershipError) -> CoroutineType[Any, Any, JSONResponse]\" is not assignable to type \"HTTPExceptionHandler\"\n      Parameter 2: type \"Exception\" is incompatible with type \"MothershipError\"\n        \"Exception\" is not assignable to \"MothershipError\"\n    Type \"(request: Request, exc: MothershipError) -> CoroutineType[Any, Any, JSONResponse]\" is not assignable to type \"WebSocketExceptionHandler\"\n      Parameter 1: type \"WebSocket\" is incompatible with type \"Request\"\n        \"WebSocket\" is not assignable to \"Request\"\n      Parameter 2: type \"Exception\" is incompatible with type \"MothershipError\"\n  ...",
	"source": "basedpyright",
	"startLineNumber": 338,
	"startColumn": 48,
	"endLineNumber": 338,
	"endColumn": 72,
	"modelVersionId": 1
},{
	"resource": "/e:/grid/application/mothership/main.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"(request: Request, exc: HTTPException) -> CoroutineType[Any, Any, JSONResponse]\" cannot be assigned to parameter \"handler\" of type \"ExceptionHandler\" in function \"add_exception_handler\"\n  Type \"(request: Request, exc: HTTPException) -> CoroutineType[Any, Any, JSONResponse]\" is not assignable to type \"ExceptionHandler\"\n    Type \"(request: Request, exc: HTTPException) -> CoroutineType[Any, Any, JSONResponse]\" is not assignable to type \"HTTPExceptionHandler\"\n      Parameter 2: type \"Exception\" is incompatible with type \"HTTPException\"\n        \"Exception\" is not assignable to \"HTTPException\"\n    Type \"(request: Request, exc: HTTPException) -> CoroutineType[Any, Any, JSONResponse]\" is not assignable to type \"WebSocketExceptionHandler\"\n      Parameter 1: type \"WebSocket\" is incompatible with type \"Request\"\n        \"WebSocket\" is not assignable to \"Request\"\n      Parameter 2: type \"Exception\" is incompatible with type \"HTTPException\"\n  ...",
	"source": "basedpyright",
	"startLineNumber": 339,
	"startColumn": 46,
	"endLineNumber": 339,
	"endColumn": 68,
	"modelVersionId": 1
},{
	"resource": "/e:/grid/application/mothership/main.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"(request: Request, exc: RequestValidationError) -> CoroutineType[Any, Any, JSONResponse]\" cannot be assigned to parameter \"handler\" of type \"ExceptionHandler\" in function \"add_exception_handler\"\n  Type \"(request: Request, exc: RequestValidationError) -> CoroutineType[Any, Any, JSONResponse]\" is not assignable to type \"ExceptionHandler\"\n    Type \"(request: Request, exc: RequestValidationError) -> CoroutineType[Any, Any, JSONResponse]\" is not assignable to type \"HTTPExceptionHandler\"\n      Parameter 2: type \"Exception\" is incompatible with type \"RequestValidationError\"\n        \"Exception\" is not assignable to \"RequestValidationError\"\n    Type \"(request: Request, exc: RequestValidationError) -> CoroutineType[Any, Any, JSONResponse]\" is not assignable to type \"WebSocketExceptionHandler\"\n      Parameter 1: type \"WebSocket\" is incompatible with type \"Request\"\n        \"WebSocket\" is not assignable to \"Request\"\n      Parameter 2: type \"Exception\" is incompatible with type \"RequestValidationError\"\n  ...",
	"source": "basedpyright",
	"startLineNumber": 340,
	"startColumn": 55,
	"endLineNumber": 340,
	"endColumn": 79,
	"modelVersionId": 1
},{
	"resource": "/e:/grid/application/mothership/main.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"grid.api.routers\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 383,
	"startColumn": 18,
	"endLineNumber": 383,
	"endColumn": 34,
	"modelVersionId": 1
},{
	"resource": "/e:/grid/application/mothership/middleware/rate_limit_redis.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportGeneralTypeIssues",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportGeneralTypeIssues"
		}
	},
	"severity": 8,
	"message": "Expected class but received \"(iterable: Iterable[object], /) -> bool\"",
	"source": "basedpyright",
	"startLineNumber": 48,
	"startColumn": 38,
	"endLineNumber": 48,
	"endColumn": 41
},{
	"resource": "/e:/grid/application/mothership/middleware/rate_limit_redis.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"redis.asyncio\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 72,
	"startColumn": 20,
	"endLineNumber": 72,
	"endColumn": 33
},{
	"resource": "/e:/grid/application/mothership/middleware/rate_limit_redis.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"ping\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 76,
	"startColumn": 38,
	"endLineNumber": 76,
	"endColumn": 42
},{
	"resource": "/e:/grid/application/mothership/middleware/rate_limit_redis.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportGeneralTypeIssues",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportGeneralTypeIssues"
		}
	},
	"severity": 8,
	"message": "Expected class but received \"(iterable: Iterable[object], /) -> bool\"",
	"source": "basedpyright",
	"startLineNumber": 150,
	"startColumn": 59,
	"endLineNumber": 150,
	"endColumn": 62
},{
	"resource": "/e:/grid/application/mothership/middleware/usage_tracking.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportGeneralTypeIssues",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportGeneralTypeIssues"
		}
	},
	"severity": 8,
	"message": "Expected class but received \"(iterable: Iterable[object], /) -> bool\"",
	"source": "basedpyright",
	"startLineNumber": 57,
	"startColumn": 59,
	"endLineNumber": 57,
	"endColumn": 62
},{
	"resource": "/e:/grid/application/mothership/repositories/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"ComponentHealth\" cannot be assigned to parameter \"health\" of type \"ComponentHealth\" in function \"update_health\"\n  \"application.mothership.models.ComponentHealth\" is not assignable to \"application.mothership.models.cockpit.ComponentHealth\"",
	"source": "basedpyright",
	"startLineNumber": 482,
	"startColumn": 37,
	"endLineNumber": 482,
	"endColumn": 43
},{
	"resource": "/e:/grid/application/mothership/repositories/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"Literal[AlertSeverity.CRITICAL]\" cannot be assigned to parameter \"severity\" of type \"AlertSeverity\" in function \"get_by_severity\"\n  \"Literal[AlertSeverity.CRITICAL]\" is not assignable to \"AlertSeverity\"",
	"source": "basedpyright",
	"startLineNumber": 555,
	"startColumn": 43,
	"endLineNumber": 555,
	"endColumn": 65
},{
	"resource": "/e:/grid/application/mothership/repositories/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"OperationMode\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 626,
	"startColumn": 37,
	"endLineNumber": 626,
	"endColumn": 50
},{
	"resource": "/e:/grid/application/mothership/repositories/api_key.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot assign to attribute \"api_keys\" for class \"StateStore\"\n  Attribute \"api_keys\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 25,
	"startColumn": 25,
	"endLineNumber": 25,
	"endColumn": 33
},{
	"resource": "/e:/grid/application/mothership/repositories/api_key.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportInvalidTypeForm",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportInvalidTypeForm"
		}
	},
	"severity": 8,
	"message": "Type annotation not supported for this statement",
	"source": "basedpyright",
	"startLineNumber": 25,
	"startColumn": 35,
	"endLineNumber": 25,
	"endColumn": 52
},{
	"resource": "/e:/grid/application/mothership/repositories/api_key.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"api_keys\" for class \"StateStore\"\n  Attribute \"api_keys\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 29,
	"startColumn": 28,
	"endLineNumber": 29,
	"endColumn": 36
},{
	"resource": "/e:/grid/application/mothership/repositories/api_key.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"api_keys\" for class \"StateStore\"\n  Attribute \"api_keys\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 33,
	"startColumn": 33,
	"endLineNumber": 33,
	"endColumn": 41
},{
	"resource": "/e:/grid/application/mothership/repositories/api_key.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"api_keys\" for class \"StateStore\"\n  Attribute \"api_keys\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 38,
	"startColumn": 25,
	"endLineNumber": 38,
	"endColumn": 33
},{
	"resource": "/e:/grid/application/mothership/repositories/api_key.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"api_keys\" for class \"StateStore\"\n  Attribute \"api_keys\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 46,
	"startColumn": 45,
	"endLineNumber": 46,
	"endColumn": 53
},{
	"resource": "/e:/grid/application/mothership/repositories/api_key.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"api_keys\" for class \"StateStore\"\n  Attribute \"api_keys\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 49,
	"startColumn": 25,
	"endLineNumber": 49,
	"endColumn": 33
},{
	"resource": "/e:/grid/application/mothership/repositories/api_key.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"api_keys\" for class \"StateStore\"\n  Attribute \"api_keys\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 55,
	"startColumn": 34,
	"endLineNumber": 55,
	"endColumn": 42
},{
	"resource": "/e:/grid/application/mothership/repositories/api_key.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"api_keys\" for class \"StateStore\"\n  Attribute \"api_keys\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 56,
	"startColumn": 33,
	"endLineNumber": 56,
	"endColumn": 41
},{
	"resource": "/e:/grid/application/mothership/repositories/api_key.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"api_keys\" for class \"StateStore\"\n  Attribute \"api_keys\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 62,
	"startColumn": 34,
	"endLineNumber": 62,
	"endColumn": 42
},{
	"resource": "/e:/grid/application/mothership/repositories/api_key.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"api_keys\" for class \"StateStore\"\n  Attribute \"api_keys\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 66,
	"startColumn": 32,
	"endLineNumber": 66,
	"endColumn": 40
},{
	"resource": "/e:/grid/application/mothership/repositories/api_key.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"api_keys\" for class \"StateStore\"\n  Attribute \"api_keys\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 70,
	"startColumn": 40,
	"endLineNumber": 70,
	"endColumn": 48
},{
	"resource": "/e:/grid/application/mothership/repositories/api_key.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"api_keys\" for class \"StateStore\"\n  Attribute \"api_keys\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 74,
	"startColumn": 32,
	"endLineNumber": 74,
	"endColumn": 40
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot assign to attribute \"payment_transactions\" for class \"StateStore\"\n  Attribute \"payment_transactions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 33,
	"startColumn": 25,
	"endLineNumber": 33,
	"endColumn": 45
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportInvalidTypeForm",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportInvalidTypeForm"
		}
	},
	"severity": 8,
	"message": "Type annotation not supported for this statement",
	"source": "basedpyright",
	"startLineNumber": 33,
	"startColumn": 47,
	"endLineNumber": 33,
	"endColumn": 76
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"payment_transactions\" for class \"StateStore\"\n  Attribute \"payment_transactions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 37,
	"startColumn": 28,
	"endLineNumber": 37,
	"endColumn": 48
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"payment_transactions\" for class \"StateStore\"\n  Attribute \"payment_transactions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 41,
	"startColumn": 33,
	"endLineNumber": 41,
	"endColumn": 53
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"payment_transactions\" for class \"StateStore\"\n  Attribute \"payment_transactions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 46,
	"startColumn": 25,
	"endLineNumber": 46,
	"endColumn": 45
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"payment_transactions\" for class \"StateStore\"\n  Attribute \"payment_transactions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 54,
	"startColumn": 45,
	"endLineNumber": 54,
	"endColumn": 65
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"payment_transactions\" for class \"StateStore\"\n  Attribute \"payment_transactions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 57,
	"startColumn": 25,
	"endLineNumber": 57,
	"endColumn": 45
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"payment_transactions\" for class \"StateStore\"\n  Attribute \"payment_transactions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 63,
	"startColumn": 34,
	"endLineNumber": 63,
	"endColumn": 54
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"payment_transactions\" for class \"StateStore\"\n  Attribute \"payment_transactions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 64,
	"startColumn": 33,
	"endLineNumber": 64,
	"endColumn": 53
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"payment_transactions\" for class \"StateStore\"\n  Attribute \"payment_transactions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 70,
	"startColumn": 34,
	"endLineNumber": 70,
	"endColumn": 54
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"payment_transactions\" for class \"StateStore\"\n  Attribute \"payment_transactions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 74,
	"startColumn": 32,
	"endLineNumber": 74,
	"endColumn": 52
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"payment_transactions\" for class \"StateStore\"\n  Attribute \"payment_transactions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 78,
	"startColumn": 40,
	"endLineNumber": 78,
	"endColumn": 60
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"payment_transactions\" for class \"StateStore\"\n  Attribute \"payment_transactions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 82,
	"startColumn": 40,
	"endLineNumber": 82,
	"endColumn": 60
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"payment_transactions\" for class \"StateStore\"\n  Attribute \"payment_transactions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 86,
	"startColumn": 30,
	"endLineNumber": 86,
	"endColumn": 50
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot assign to attribute \"subscriptions\" for class \"StateStore\"\n  Attribute \"subscriptions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 98,
	"startColumn": 25,
	"endLineNumber": 98,
	"endColumn": 38
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportInvalidTypeForm",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportInvalidTypeForm"
		}
	},
	"severity": 8,
	"message": "Type annotation not supported for this statement",
	"source": "basedpyright",
	"startLineNumber": 98,
	"startColumn": 40,
	"endLineNumber": 98,
	"endColumn": 63
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"subscriptions\" for class \"StateStore\"\n  Attribute \"subscriptions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 102,
	"startColumn": 28,
	"endLineNumber": 102,
	"endColumn": 41
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"subscriptions\" for class \"StateStore\"\n  Attribute \"subscriptions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 106,
	"startColumn": 33,
	"endLineNumber": 106,
	"endColumn": 46
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"subscriptions\" for class \"StateStore\"\n  Attribute \"subscriptions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 111,
	"startColumn": 25,
	"endLineNumber": 111,
	"endColumn": 38
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"subscriptions\" for class \"StateStore\"\n  Attribute \"subscriptions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 119,
	"startColumn": 45,
	"endLineNumber": 119,
	"endColumn": 58
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"subscriptions\" for class \"StateStore\"\n  Attribute \"subscriptions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 122,
	"startColumn": 25,
	"endLineNumber": 122,
	"endColumn": 38
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"subscriptions\" for class \"StateStore\"\n  Attribute \"subscriptions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 128,
	"startColumn": 34,
	"endLineNumber": 128,
	"endColumn": 47
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"subscriptions\" for class \"StateStore\"\n  Attribute \"subscriptions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 129,
	"startColumn": 33,
	"endLineNumber": 129,
	"endColumn": 46
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"subscriptions\" for class \"StateStore\"\n  Attribute \"subscriptions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 135,
	"startColumn": 34,
	"endLineNumber": 135,
	"endColumn": 47
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"subscriptions\" for class \"StateStore\"\n  Attribute \"subscriptions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 139,
	"startColumn": 32,
	"endLineNumber": 139,
	"endColumn": 45
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"subscriptions\" for class \"StateStore\"\n  Attribute \"subscriptions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 143,
	"startColumn": 40,
	"endLineNumber": 143,
	"endColumn": 53
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"subscriptions\" for class \"StateStore\"\n  Attribute \"subscriptions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 147,
	"startColumn": 32,
	"endLineNumber": 147,
	"endColumn": 45
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"subscriptions\" for class \"StateStore\"\n  Attribute \"subscriptions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 154,
	"startColumn": 40,
	"endLineNumber": 154,
	"endColumn": 53
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"subscriptions\" for class \"StateStore\"\n  Attribute \"subscriptions\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 158,
	"startColumn": 40,
	"endLineNumber": 158,
	"endColumn": 53
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot assign to attribute \"invoices\" for class \"StateStore\"\n  Attribute \"invoices\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 167,
	"startColumn": 25,
	"endLineNumber": 167,
	"endColumn": 33
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportInvalidTypeForm",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportInvalidTypeForm"
		}
	},
	"severity": 8,
	"message": "Type annotation not supported for this statement",
	"source": "basedpyright",
	"startLineNumber": 167,
	"startColumn": 35,
	"endLineNumber": 167,
	"endColumn": 53
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"invoices\" for class \"StateStore\"\n  Attribute \"invoices\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 171,
	"startColumn": 28,
	"endLineNumber": 171,
	"endColumn": 36
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"invoices\" for class \"StateStore\"\n  Attribute \"invoices\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 175,
	"startColumn": 33,
	"endLineNumber": 175,
	"endColumn": 41
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"invoices\" for class \"StateStore\"\n  Attribute \"invoices\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 180,
	"startColumn": 25,
	"endLineNumber": 180,
	"endColumn": 33
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"invoices\" for class \"StateStore\"\n  Attribute \"invoices\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 188,
	"startColumn": 45,
	"endLineNumber": 188,
	"endColumn": 53
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"invoices\" for class \"StateStore\"\n  Attribute \"invoices\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 191,
	"startColumn": 25,
	"endLineNumber": 191,
	"endColumn": 33
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"invoices\" for class \"StateStore\"\n  Attribute \"invoices\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 197,
	"startColumn": 34,
	"endLineNumber": 197,
	"endColumn": 42
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"invoices\" for class \"StateStore\"\n  Attribute \"invoices\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 198,
	"startColumn": 33,
	"endLineNumber": 198,
	"endColumn": 41
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"invoices\" for class \"StateStore\"\n  Attribute \"invoices\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 204,
	"startColumn": 34,
	"endLineNumber": 204,
	"endColumn": 42
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"invoices\" for class \"StateStore\"\n  Attribute \"invoices\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 208,
	"startColumn": 32,
	"endLineNumber": 208,
	"endColumn": 40
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"invoices\" for class \"StateStore\"\n  Attribute \"invoices\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 212,
	"startColumn": 40,
	"endLineNumber": 212,
	"endColumn": 48
},{
	"resource": "/e:/grid/application/mothership/repositories/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"invoices\" for class \"StateStore\"\n  Attribute \"invoices\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 216,
	"startColumn": 40,
	"endLineNumber": 216,
	"endColumn": 48
},{
	"resource": "/e:/grid/application/mothership/repositories/usage.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot assign to attribute \"usage_records\" for class \"StateStore\"\n  Attribute \"usage_records\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 25,
	"startColumn": 25,
	"endLineNumber": 25,
	"endColumn": 38
},{
	"resource": "/e:/grid/application/mothership/repositories/usage.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportInvalidTypeForm",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportInvalidTypeForm"
		}
	},
	"severity": 8,
	"message": "Type annotation not supported for this statement",
	"source": "basedpyright",
	"startLineNumber": 25,
	"startColumn": 40,
	"endLineNumber": 25,
	"endColumn": 62
},{
	"resource": "/e:/grid/application/mothership/repositories/usage.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"usage_records\" for class \"StateStore\"\n  Attribute \"usage_records\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 29,
	"startColumn": 28,
	"endLineNumber": 29,
	"endColumn": 41
},{
	"resource": "/e:/grid/application/mothership/repositories/usage.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"usage_records\" for class \"StateStore\"\n  Attribute \"usage_records\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 33,
	"startColumn": 33,
	"endLineNumber": 33,
	"endColumn": 46
},{
	"resource": "/e:/grid/application/mothership/repositories/usage.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"usage_records\" for class \"StateStore\"\n  Attribute \"usage_records\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 38,
	"startColumn": 25,
	"endLineNumber": 38,
	"endColumn": 38
},{
	"resource": "/e:/grid/application/mothership/repositories/usage.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"usage_records\" for class \"StateStore\"\n  Attribute \"usage_records\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 44,
	"startColumn": 45,
	"endLineNumber": 44,
	"endColumn": 58
},{
	"resource": "/e:/grid/application/mothership/repositories/usage.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"usage_records\" for class \"StateStore\"\n  Attribute \"usage_records\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 46,
	"startColumn": 25,
	"endLineNumber": 46,
	"endColumn": 38
},{
	"resource": "/e:/grid/application/mothership/repositories/usage.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"usage_records\" for class \"StateStore\"\n  Attribute \"usage_records\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 52,
	"startColumn": 34,
	"endLineNumber": 52,
	"endColumn": 47
},{
	"resource": "/e:/grid/application/mothership/repositories/usage.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"usage_records\" for class \"StateStore\"\n  Attribute \"usage_records\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 53,
	"startColumn": 33,
	"endLineNumber": 53,
	"endColumn": 46
},{
	"resource": "/e:/grid/application/mothership/repositories/usage.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"usage_records\" for class \"StateStore\"\n  Attribute \"usage_records\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 59,
	"startColumn": 34,
	"endLineNumber": 59,
	"endColumn": 47
},{
	"resource": "/e:/grid/application/mothership/repositories/usage.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"usage_records\" for class \"StateStore\"\n  Attribute \"usage_records\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 63,
	"startColumn": 32,
	"endLineNumber": 63,
	"endColumn": 45
},{
	"resource": "/e:/grid/application/mothership/repositories/usage.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"usage_records\" for class \"StateStore\"\n  Attribute \"usage_records\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 69,
	"startColumn": 43,
	"endLineNumber": 69,
	"endColumn": 56
},{
	"resource": "/e:/grid/application/mothership/routers/api_keys.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"Annotated\" cannot be assigned to parameter of type \"dict[Unknown, Unknown]\"\n  \"Annotated\" is not assignable to \"dict[Unknown, Unknown]\"",
	"source": "basedpyright",
	"startLineNumber": 73,
	"startColumn": 18,
	"endLineNumber": 73,
	"endColumn": 30
},{
	"resource": "/e:/grid/application/mothership/routers/api_keys.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"Annotated\" cannot be assigned to parameter of type \"dict[Unknown, Unknown]\"\n  \"Annotated\" is not assignable to \"dict[Unknown, Unknown]\"",
	"source": "basedpyright",
	"startLineNumber": 115,
	"startColumn": 18,
	"endLineNumber": 115,
	"endColumn": 30
},{
	"resource": "/e:/grid/application/mothership/routers/api_keys.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"Annotated\" cannot be assigned to parameter of type \"dict[Unknown, Unknown]\"\n  \"Annotated\" is not assignable to \"dict[Unknown, Unknown]\"",
	"source": "basedpyright",
	"startLineNumber": 127,
	"startColumn": 18,
	"endLineNumber": 127,
	"endColumn": 30
},{
	"resource": "/e:/grid/application/mothership/routers/api_keys.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"Annotated\" cannot be assigned to parameter of type \"dict[Unknown, Unknown]\"\n  \"Annotated\" is not assignable to \"dict[Unknown, Unknown]\"",
	"source": "basedpyright",
	"startLineNumber": 149,
	"startColumn": 18,
	"endLineNumber": 149,
	"endColumn": 30
},{
	"resource": "/e:/grid/application/mothership/routers/api_keys.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"Annotated\" cannot be assigned to parameter of type \"dict[Unknown, Unknown]\"\n  \"Annotated\" is not assignable to \"dict[Unknown, Unknown]\"",
	"source": "basedpyright",
	"startLineNumber": 177,
	"startColumn": 18,
	"endLineNumber": 177,
	"endColumn": 30
},{
	"resource": "/e:/grid/application/mothership/routers/billing.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"Annotated\" cannot be assigned to parameter of type \"dict[Unknown, Unknown]\"\n  \"Annotated\" is not assignable to \"dict[Unknown, Unknown]\"",
	"source": "basedpyright",
	"startLineNumber": 29,
	"startColumn": 18,
	"endLineNumber": 29,
	"endColumn": 30
},{
	"resource": "/e:/grid/application/mothership/routers/billing.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"Annotated\" cannot be assigned to parameter of type \"dict[Unknown, Unknown]\"\n  \"Annotated\" is not assignable to \"dict[Unknown, Unknown]\"",
	"source": "basedpyright",
	"startLineNumber": 44,
	"startColumn": 18,
	"endLineNumber": 44,
	"endColumn": 30
},{
	"resource": "/e:/grid/application/mothership/routers/billing.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"Annotated\" cannot be assigned to parameter of type \"dict[Unknown, Unknown]\"\n  \"Annotated\" is not assignable to \"dict[Unknown, Unknown]\"",
	"source": "basedpyright",
	"startLineNumber": 56,
	"startColumn": 18,
	"endLineNumber": 56,
	"endColumn": 30
},{
	"resource": "/e:/grid/application/mothership/routers/cockpit.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"type | Literal['warning']\" cannot be assigned to parameter \"severity\" of type \"AlertSeverity\" in function \"create_alert\"\n  Type \"type | Literal['warning']\" is not assignable to type \"AlertSeverity\"\n    \"Literal['warning']\" is not assignable to \"AlertSeverity\"",
	"source": "basedpyright",
	"startLineNumber": 633,
	"startColumn": 18,
	"endLineNumber": 637,
	"endColumn": 10
},{
	"resource": "/e:/grid/application/mothership/routers/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"Annotated\" cannot be assigned to parameter of type \"dict[Unknown, Unknown]\"\n  \"Annotated\" is not assignable to \"dict[Unknown, Unknown]\"",
	"source": "basedpyright",
	"startLineNumber": 110,
	"startColumn": 18,
	"endLineNumber": 110,
	"endColumn": 30,
	"modelVersionId": 1
},{
	"resource": "/e:/grid/application/mothership/routers/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"Annotated\" cannot be assigned to parameter of type \"Settings\"\n  \"Annotated\" is not assignable to \"MothershipSettings\"",
	"source": "basedpyright",
	"startLineNumber": 111,
	"startColumn": 26,
	"endLineNumber": 111,
	"endColumn": 34,
	"modelVersionId": 1
},{
	"resource": "/e:/grid/application/mothership/routers/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportCallIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportCallIssue"
		}
	},
	"severity": 8,
	"message": "Arguments missing for parameters \"client_secret\", \"payment_url\"",
	"source": "basedpyright",
	"startLineNumber": 126,
	"startColumn": 24,
	"endLineNumber": 126,
	"endColumn": 107,
	"modelVersionId": 1
},{
	"resource": "/e:/grid/application/mothership/routers/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"Any | None\" cannot be assigned to parameter \"idempotency_key\" of type \"str\" in function \"__init__\"\n  Type \"Any | None\" is not assignable to type \"str\"\n    \"None\" is not assignable to \"str\"",
	"source": "basedpyright",
	"startLineNumber": 148,
	"startColumn": 29,
	"endLineNumber": 148,
	"endColumn": 44,
	"modelVersionId": 1
},{
	"resource": "/e:/grid/application/mothership/routers/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"Annotated\" cannot be assigned to parameter of type \"Settings\"\n  \"Annotated\" is not assignable to \"MothershipSettings\"",
	"source": "basedpyright",
	"startLineNumber": 174,
	"startColumn": 26,
	"endLineNumber": 174,
	"endColumn": 34,
	"modelVersionId": 1
},{
	"resource": "/e:/grid/application/mothership/routers/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"Annotated\" cannot be assigned to parameter of type \"dict[Unknown, Unknown]\"\n  \"Annotated\" is not assignable to \"dict[Unknown, Unknown]\"",
	"source": "basedpyright",
	"startLineNumber": 230,
	"startColumn": 18,
	"endLineNumber": 230,
	"endColumn": 30,
	"modelVersionId": 1
},{
	"resource": "/e:/grid/application/mothership/routers/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"Annotated\" cannot be assigned to parameter of type \"dict[Unknown, Unknown]\"\n  \"Annotated\" is not assignable to \"dict[Unknown, Unknown]\"",
	"source": "basedpyright",
	"startLineNumber": 251,
	"startColumn": 18,
	"endLineNumber": 251,
	"endColumn": 30,
	"modelVersionId": 1
},{
	"resource": "/e:/grid/application/mothership/routers/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"Annotated\" cannot be assigned to parameter of type \"Settings\"\n  \"Annotated\" is not assignable to \"MothershipSettings\"",
	"source": "basedpyright",
	"startLineNumber": 252,
	"startColumn": 26,
	"endLineNumber": 252,
	"endColumn": 34,
	"modelVersionId": 1
},{
	"resource": "/e:/grid/application/mothership/routers/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"Annotated\" cannot be assigned to parameter of type \"dict[Unknown, Unknown]\"\n  \"Annotated\" is not assignable to \"dict[Unknown, Unknown]\"",
	"source": "basedpyright",
	"startLineNumber": 307,
	"startColumn": 18,
	"endLineNumber": 307,
	"endColumn": 30,
	"modelVersionId": 1
},{
	"resource": "/e:/grid/application/mothership/routers/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"Annotated\" cannot be assigned to parameter of type \"Settings\"\n  \"Annotated\" is not assignable to \"MothershipSettings\"",
	"source": "basedpyright",
	"startLineNumber": 308,
	"startColumn": 26,
	"endLineNumber": 308,
	"endColumn": 34,
	"modelVersionId": 1
},{
	"resource": "/e:/grid/application/mothership/routers/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnboundVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnboundVariable"
		}
	},
	"severity": 8,
	"message": "\"user_id\" is unbound",
	"source": "basedpyright",
	"startLineNumber": 315,
	"startColumn": 21,
	"endLineNumber": 315,
	"endColumn": 28,
	"modelVersionId": 1
},{
	"resource": "/e:/grid/application/mothership/routers/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"Annotated\" cannot be assigned to parameter of type \"dict[Unknown, Unknown]\"\n  \"Annotated\" is not assignable to \"dict[Unknown, Unknown]\"",
	"source": "basedpyright",
	"startLineNumber": 351,
	"startColumn": 18,
	"endLineNumber": 351,
	"endColumn": 30,
	"modelVersionId": 1
},{
	"resource": "/e:/grid/application/mothership/routers/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"user_id\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 360,
	"startColumn": 32,
	"endLineNumber": 360,
	"endColumn": 39,
	"modelVersionId": 1
},{
	"resource": "/e:/grid/application/mothership/routers/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"Annotated\" cannot be assigned to parameter of type \"dict[Unknown, Unknown]\"\n  \"Annotated\" is not assignable to \"dict[Unknown, Unknown]\"",
	"source": "basedpyright",
	"startLineNumber": 396,
	"startColumn": 18,
	"endLineNumber": 396,
	"endColumn": 30,
	"modelVersionId": 1
},{
	"resource": "/e:/grid/application/mothership/routers/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"user_id\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 404,
	"startColumn": 32,
	"endLineNumber": 404,
	"endColumn": 39,
	"modelVersionId": 1
},{
	"resource": "/e:/grid/application/mothership/routers/payment.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"Annotated\" cannot be assigned to parameter of type \"dict[Unknown, Unknown]\"\n  \"Annotated\" is not assignable to \"dict[Unknown, Unknown]\"",
	"source": "basedpyright",
	"startLineNumber": 415,
	"startColumn": 18,
	"endLineNumber": 415,
	"endColumn": 30,
	"modelVersionId": 1
},{
	"resource": "/e:/grid/application/mothership/services/payment/stripe_gateway.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"stripe\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 13,
	"startColumn": 12,
	"endLineNumber": 13,
	"endColumn": 18
},{
	"resource": "/e:/grid/application/mothership/services/payment/stripe_gateway.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"PaymentIntent\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 65,
	"startColumn": 29,
	"endLineNumber": 65,
	"endColumn": 42
},{
	"resource": "/e:/grid/application/mothership/services/payment/stripe_gateway.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"error\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 80,
	"startColumn": 23,
	"endLineNumber": 80,
	"endColumn": 28
},{
	"resource": "/e:/grid/application/mothership/services/payment/stripe_gateway.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"Webhook\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 91,
	"startColumn": 28,
	"endLineNumber": 91,
	"endColumn": 35
},{
	"resource": "/e:/grid/application/mothership/services/payment/stripe_gateway.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"error\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 101,
	"startColumn": 23,
	"endLineNumber": 101,
	"endColumn": 28
},{
	"resource": "/e:/grid/application/mothership/services/payment/stripe_gateway.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"PaymentIntent\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 108,
	"startColumn": 29,
	"endLineNumber": 108,
	"endColumn": 42
},{
	"resource": "/e:/grid/application/mothership/services/payment/stripe_gateway.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"error\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 119,
	"startColumn": 23,
	"endLineNumber": 119,
	"endColumn": 28
},{
	"resource": "/e:/grid/application/mothership/services/payment/stripe_gateway.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"Subscription\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 152,
	"startColumn": 35,
	"endLineNumber": 152,
	"endColumn": 47
},{
	"resource": "/e:/grid/application/mothership/services/payment/stripe_gateway.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"error\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 160,
	"startColumn": 23,
	"endLineNumber": 160,
	"endColumn": 28
},{
	"resource": "/e:/grid/application/mothership/services/payment/stripe_gateway.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"Subscription\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 172,
	"startColumn": 24,
	"endLineNumber": 172,
	"endColumn": 36
},{
	"resource": "/e:/grid/application/mothership/services/payment/stripe_gateway.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"Subscription\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 174,
	"startColumn": 24,
	"endLineNumber": 174,
	"endColumn": 36
},{
	"resource": "/e:/grid/application/mothership/services/payment/stripe_gateway.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"error\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 176,
	"startColumn": 23,
	"endLineNumber": 176,
	"endColumn": 28
},{
	"resource": "/e:/grid/application/mothership/services/payment/stripe_gateway.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"Refund\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 197,
	"startColumn": 29,
	"endLineNumber": 197,
	"endColumn": 35
},{
	"resource": "/e:/grid/application/mothership/services/payment/stripe_gateway.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"error\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 205,
	"startColumn": 23,
	"endLineNumber": 205,
	"endColumn": 28
},{
	"resource": "/e:/grid/application/resonance/activity_resonance.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"str | None\" cannot be assigned to parameter \"application_path\" of type \"Path | None\" in function \"__init__\"\n  Type \"str | None\" is not assignable to type \"Path | None\"\n    Type \"str\" is not assignable to type \"Path | None\"\n      \"str\" is not assignable to \"Path\"\n      \"str\" is not assignable to \"None\"",
	"source": "basedpyright",
	"startLineNumber": 89,
	"startColumn": 49,
	"endLineNumber": 89,
	"endColumn": 65
},{
	"resource": "/e:/grid/application/resonance/activity_resonance.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"str | None\" cannot be assigned to parameter \"light_path\" of type \"Path | None\" in function \"__init__\"\n  Type \"str | None\" is not assignable to type \"Path | None\"\n    Type \"str\" is not assignable to type \"Path | None\"\n      \"str\" is not assignable to \"Path\"\n      \"str\" is not assignable to \"None\"",
	"source": "basedpyright",
	"startLineNumber": 90,
	"startColumn": 47,
	"endLineNumber": 90,
	"endColumn": 57
},{
	"resource": "/e:/grid/application/resonance/api/performance.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"sqlalchemy.orm\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 10,
	"endLineNumber": 7,
	"endColumn": 24
},{
	"resource": "/e:/grid/application/resonance/api/performance.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"sqlalchemy\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 8,
	"startColumn": 10,
	"endLineNumber": 8,
	"endColumn": 20
},{
	"resource": "/e:/grid/application/resonance/api/performance.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "\"get_db\" is unknown import symbol",
	"source": "basedpyright",
	"startLineNumber": 17,
	"startColumn": 47,
	"endLineNumber": 17,
	"endColumn": 53
},{
	"resource": "/e:/grid/application/resonance/api/performance.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportInvalidTypeForm",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportInvalidTypeForm"
		}
	},
	"severity": 8,
	"message": "Variable not allowed in type expression",
	"source": "basedpyright",
	"startLineNumber": 44,
	"startColumn": 30,
	"endLineNumber": 44,
	"endColumn": 37
},{
	"resource": "/e:/grid/application/resonance/api/performance.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportInvalidTypeForm",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportInvalidTypeForm"
		}
	},
	"severity": 8,
	"message": "Variable not allowed in type expression",
	"source": "basedpyright",
	"startLineNumber": 72,
	"startColumn": 33,
	"endLineNumber": 72,
	"endColumn": 40
},{
	"resource": "/e:/grid/application/resonance/api/performance.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportInvalidTypeForm",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportInvalidTypeForm"
		}
	},
	"severity": 8,
	"message": "Variable not allowed in type expression",
	"source": "basedpyright",
	"startLineNumber": 101,
	"startColumn": 32,
	"endLineNumber": 101,
	"endColumn": 39
},{
	"resource": "/e:/grid/application/resonance/api/performance.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportInvalidTypeForm",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportInvalidTypeForm"
		}
	},
	"severity": 8,
	"message": "Variable not allowed in type expression",
	"source": "basedpyright",
	"startLineNumber": 129,
	"startColumn": 36,
	"endLineNumber": 129,
	"endColumn": 43
},{
	"resource": "/e:/grid/application/resonance/api/router.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"None\" cannot be assigned to parameter of type \"ResonanceServiceDep\"\n  \"None\" is not assignable to \"ResonanceService\"",
	"source": "basedpyright",
	"startLineNumber": 240,
	"startColumn": 36,
	"endLineNumber": 240,
	"endColumn": 40
},{
	"resource": "/e:/grid/application/resonance/api/router.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"None\" cannot be assigned to parameter of type \"ResonanceServiceDep\"\n  \"None\" is not assignable to \"ResonanceService\"",
	"source": "basedpyright",
	"startLineNumber": 273,
	"startColumn": 36,
	"endLineNumber": 273,
	"endColumn": 40
},{
	"resource": "/e:/grid/application/resonance/api/router.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"None\" cannot be assigned to parameter of type \"ResonanceServiceDep\"\n  \"None\" is not assignable to \"ResonanceService\"",
	"source": "basedpyright",
	"startLineNumber": 305,
	"startColumn": 36,
	"endLineNumber": 305,
	"endColumn": 40
},{
	"resource": "/e:/grid/application/resonance/api/router.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"None\" cannot be assigned to parameter of type \"ResonanceServiceDep\"\n  \"None\" is not assignable to \"ResonanceService\"",
	"source": "basedpyright",
	"startLineNumber": 340,
	"startColumn": 36,
	"endLineNumber": 340,
	"endColumn": 40
},{
	"resource": "/e:/grid/application/resonance/api/router.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"None\" cannot be assigned to parameter of type \"ResonanceServiceDep\"\n  \"None\" is not assignable to \"ResonanceService\"",
	"source": "basedpyright",
	"startLineNumber": 381,
	"startColumn": 36,
	"endLineNumber": 381,
	"endColumn": 40
},{
	"resource": "/e:/grid/application/resonance/api/router.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"API_REQUEST\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 446,
	"startColumn": 32,
	"endLineNumber": 446,
	"endColumn": 43
},{
	"resource": "/e:/grid/application/resonance/api/router.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"..config\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 745,
	"startColumn": 10,
	"endLineNumber": 745,
	"endColumn": 18
},{
	"resource": "/e:/grid/application/resonance/cli.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"path_visualizer\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 219,
	"startColumn": 38,
	"endLineNumber": 219,
	"endColumn": 53
},{
	"resource": "/e:/grid/application/resonance/cli.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"id\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 224,
	"startColumn": 77,
	"endLineNumber": 224,
	"endColumn": 79
},{
	"resource": "/e:/grid/archival/atmosphere/Atmosphere/src/proxy_bypass_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportCallIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportCallIssue"
		}
	},
	"severity": 8,
	"message": "No parameter named \"proxies\"",
	"source": "basedpyright",
	"startLineNumber": 38,
	"startColumn": 9,
	"endLineNumber": 38,
	"endColumn": 16
},{
	"resource": "/e:/grid/archival/atmosphere/Atmosphere/src/proxy_bypass_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportCallIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportCallIssue"
		}
	},
	"severity": 8,
	"message": "No parameter named \"proxies\"",
	"source": "basedpyright",
	"startLineNumber": 67,
	"startColumn": 9,
	"endLineNumber": 67,
	"endColumn": 16
},{
	"resource": "/e:/grid/archival/atmosphere/Atmosphere/src/proxy_bypass_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"_proxies\" for class \"Client\"\n  Attribute \"_proxies\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 129,
	"startColumn": 53,
	"endLineNumber": 129,
	"endColumn": 61
},{
	"resource": "/e:/grid/archival/atmosphere/Atmosphere/src/proxy_bypass_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"_proxies\" for class \"AsyncClient\"\n  Attribute \"_proxies\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 129,
	"startColumn": 53,
	"endLineNumber": 129,
	"endColumn": 61
},{
	"resource": "/e:/grid/archival/atmosphere/Atmosphere/src/proxy_bypass_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"_proxies\" for class \"Client\"\n  Attribute \"_proxies\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 129,
	"startColumn": 80,
	"endLineNumber": 129,
	"endColumn": 88
},{
	"resource": "/e:/grid/archival/atmosphere/Atmosphere/src/proxy_bypass_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"_proxies\" for class \"AsyncClient\"\n  Attribute \"_proxies\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 129,
	"startColumn": 80,
	"endLineNumber": 129,
	"endColumn": 88
},{
	"resource": "/e:/grid/archival/atmosphere/Atmosphere/src/proxy_bypass_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"proxies\" for class \"Client\"\n  Attribute \"proxies\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 131,
	"startColumn": 53,
	"endLineNumber": 131,
	"endColumn": 60
},{
	"resource": "/e:/grid/archival/atmosphere/Atmosphere/src/proxy_bypass_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"proxies\" for class \"AsyncClient\"\n  Attribute \"proxies\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 131,
	"startColumn": 53,
	"endLineNumber": 131,
	"endColumn": 60
},{
	"resource": "/e:/grid/archival/atmosphere/Atmosphere/src/proxy_bypass_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"proxies\" for class \"Client\"\n  Attribute \"proxies\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 131,
	"startColumn": 79,
	"endLineNumber": 131,
	"endColumn": 86
},{
	"resource": "/e:/grid/archival/atmosphere/Atmosphere/src/proxy_bypass_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"proxies\" for class \"AsyncClient\"\n  Attribute \"proxies\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 131,
	"startColumn": 79,
	"endLineNumber": 131,
	"endColumn": 86
},{
	"resource": "/e:/grid/archival/debug/debug_articulation.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.kernel.bus\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 6,
	"endLineNumber": 1,
	"endColumn": 25
},{
	"resource": "/e:/grid/archival/debug/debug_articulation.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.plugins.articulation\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 6,
	"endLineNumber": 7,
	"endColumn": 35
},{
	"resource": "/e:/grid/archival/debug/debug_articulation2.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.kernel.bus\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 6,
	"endLineNumber": 1,
	"endColumn": 25
},{
	"resource": "/e:/grid/archival/debug/debug_articulation2.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.plugins.articulation\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 6,
	"endLineNumber": 7,
	"endColumn": 35
},{
	"resource": "/e:/grid/archival/debug/debug_articulation3.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.kernel.bus\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 6,
	"endLineNumber": 1,
	"endColumn": 25
},{
	"resource": "/e:/grid/archival/debug/debug_articulation3.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.plugins.articulation\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 6,
	"endLineNumber": 7,
	"endColumn": 35
},{
	"resource": "/e:/grid/archival/debug/debug_physics.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.kernel.bus\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 6,
	"endLineNumber": 1,
	"endColumn": 25
},{
	"resource": "/e:/grid/archival/debug/debug_physics.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.plugins.physics\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 6,
	"endLineNumber": 7,
	"endColumn": 30
},{
	"resource": "/e:/grid/archival/debug/debug_physics.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.kernel.bus\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 13,
	"startColumn": 14,
	"endLineNumber": 13,
	"endColumn": 33
},{
	"resource": "/e:/grid/archival/experiments/example_codestral_usage.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"grid.codestral_client\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 12,
	"startColumn": 6,
	"endLineNumber": 12,
	"endColumn": 27
},{
	"resource": "/e:/grid/archival/experiments/ner_upgrade_plan.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"None\" is not assignable to declared type \"List[str]\"\n  \"None\" is not assignable to \"List[str]\"",
	"source": "basedpyright",
	"startLineNumber": 32,
	"startColumn": 31,
	"endLineNumber": 32,
	"endColumn": 35
},{
	"resource": "/e:/grid/archival/experiments/watch_module_0.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"float\" is not assignable to declared type \"int\"\n  \"float\" is not assignable to \"int\"",
	"source": "basedpyright",
	"startLineNumber": 83,
	"startColumn": 22,
	"endLineNumber": 83,
	"endColumn": 26
},{
	"resource": "/e:/grid/archival/experiments/watch_module_1.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"None\" cannot be assigned to parameter of type \"int\"\n  \"None\" is not assignable to \"int\"",
	"source": "basedpyright",
	"startLineNumber": 111,
	"startColumn": 35,
	"endLineNumber": 111,
	"endColumn": 39
},{
	"resource": "/e:/grid/archival/experiments/watch_module_1.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"int | None\" cannot be assigned to parameter \"duration\" of type \"int\" in function \"run\"\n  Type \"int | None\" is not assignable to type \"int\"\n    \"None\" is not assignable to \"int\"",
	"source": "basedpyright",
	"startLineNumber": 169,
	"startColumn": 24,
	"endLineNumber": 169,
	"endColumn": 32
},{
	"resource": "/e:/grid/archival/experiments/watch_module_2.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"int | None\" cannot be assigned to parameter \"duration\" of type \"int\" in function \"run\"\n  Type \"int | None\" is not assignable to type \"int\"\n    \"None\" is not assignable to \"int\"",
	"source": "basedpyright",
	"startLineNumber": 203,
	"startColumn": 24,
	"endLineNumber": 203,
	"endColumn": 32
},{
	"resource": "/e:/grid/archival/experiments/watch_module_4_audio.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"int | None\" cannot be assigned to parameter \"duration\" of type \"int\" in function \"run\"\n  Type \"int | None\" is not assignable to type \"int\"\n    \"None\" is not assignable to \"int\"",
	"source": "basedpyright",
	"startLineNumber": 251,
	"startColumn": 26,
	"endLineNumber": 251,
	"endColumn": 34
},{
	"resource": "/e:/grid/archival/python_unclear/Python/ide_recorder_cli.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.ide_recorder\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 21,
	"startColumn": 6,
	"endLineNumber": 21,
	"endColumn": 27
},{
	"resource": "/e:/grid/archival/python_unclear/Python/ide_recorder_cli.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.ide_recorder.events\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 30,
	"startColumn": 6,
	"endLineNumber": 30,
	"endColumn": 34
},{
	"resource": "/e:/grid/archival/python_unclear/Python/ide_recorder_cli.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.ide_recorder.narrator\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 31,
	"startColumn": 6,
	"endLineNumber": 31,
	"endColumn": 36
},{
	"resource": "/e:/grid/archival/python_unclear/Python/ide_recorder_cli.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.ide_recorder.uploader\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 32,
	"startColumn": 6,
	"endLineNumber": 32,
	"endColumn": 36
},{
	"resource": "/e:/grid/archival/python_unclear/Python/run_variant_simulation.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"None\" is not assignable to declared type \"List[str]\"\n  \"None\" is not assignable to \"List[str]\"",
	"source": "basedpyright",
	"startLineNumber": 49,
	"startColumn": 29,
	"endLineNumber": 49,
	"endColumn": 33
},{
	"resource": "/e:/grid/archival/python_unclear/Python/run_variant_simulation.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"None\" cannot be assigned to parameter of type \"int\"\n  \"None\" is not assignable to \"int\"",
	"source": "basedpyright",
	"startLineNumber": 111,
	"startColumn": 52,
	"endLineNumber": 111,
	"endColumn": 56
},{
	"resource": "/e:/grid/archival/python_unclear/Python/sora_prompt_generator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"error_patterns\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 609,
	"startColumn": 27,
	"endLineNumber": 609,
	"endColumn": 41
},{
	"resource": "/e:/grid/archival/python_unclear/Python/sora_prompt_generator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"error_patterns\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 610,
	"startColumn": 30,
	"endLineNumber": 610,
	"endColumn": 44
},{
	"resource": "/e:/grid/archival/python_unclear/Python/src/dice.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.logger\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 6,
	"startColumn": 6,
	"endLineNumber": 6,
	"endColumn": 21
},{
	"resource": "/e:/grid/archival/python_unclear/Python/src/ide_recorder/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.ide_recorder.config\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 21,
	"startColumn": 6,
	"endLineNumber": 21,
	"endColumn": 34
},{
	"resource": "/e:/grid/archival/python_unclear/Python/src/ide_recorder/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.ide_recorder.events\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 22,
	"startColumn": 6,
	"endLineNumber": 22,
	"endColumn": 34
},{
	"resource": "/e:/grid/archival/python_unclear/Python/src/ide_recorder/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.ide_recorder.narrator\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 23,
	"startColumn": 6,
	"endLineNumber": 23,
	"endColumn": 36
},{
	"resource": "/e:/grid/archival/python_unclear/Python/src/ide_recorder/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.ide_recorder.recorder\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 24,
	"startColumn": 6,
	"endLineNumber": 24,
	"endColumn": 36
},{
	"resource": "/e:/grid/archival/python_unclear/Python/src/ide_recorder/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.ide_recorder.timeline\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 25,
	"startColumn": 6,
	"endLineNumber": 25,
	"endColumn": 36
},{
	"resource": "/e:/grid/archival/python_unclear/Python/src/ide_recorder/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.ide_recorder.uploader\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 26,
	"startColumn": 6,
	"endLineNumber": 26,
	"endColumn": 36
},{
	"resource": "/e:/grid/archival/python_unclear/Python/src/ide_recorder/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.ide_recorder.video_processor\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 27,
	"startColumn": 6,
	"endLineNumber": 27,
	"endColumn": 43
},{
	"resource": "/e:/grid/archival/python_unclear/Python/src/ide_recorder/narrator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "\"ChatCompletion\" is not a known attribute of module \"openai\"",
	"source": "basedpyright",
	"startLineNumber": 208,
	"startColumn": 31,
	"endLineNumber": 208,
	"endColumn": 45
},{
	"resource": "/e:/grid/archival/python_unclear/Python/src/ide_recorder/narrator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"anthropic\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 233,
	"startColumn": 20,
	"endLineNumber": 233,
	"endColumn": 29
},{
	"resource": "/e:/grid/archival/python_unclear/Python/src/ide_recorder/narrator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"google.generativeai\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 260,
	"startColumn": 20,
	"endLineNumber": 260,
	"endColumn": 39
},{
	"resource": "/e:/grid/archival/python_unclear/Python/src/ide_recorder/narrator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "\"Audio\" is not a known attribute of module \"openai\"",
	"source": "basedpyright",
	"startLineNumber": 324,
	"startColumn": 31,
	"endLineNumber": 324,
	"endColumn": 36
},{
	"resource": "/e:/grid/archival/python_unclear/Python/src/ide_recorder/narrator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "\"texttospeech\" is unknown import symbol",
	"source": "basedpyright",
	"startLineNumber": 353,
	"startColumn": 38,
	"endLineNumber": 353,
	"endColumn": 50
},{
	"resource": "/e:/grid/archival/python_unclear/Python/src/ide_recorder/timeline.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.ide_recorder.events\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 21,
	"startColumn": 6,
	"endLineNumber": 21,
	"endColumn": 34
},{
	"resource": "/e:/grid/archival/python_unclear/Python/src/ide_recorder/timeline.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"Unknown | datetime | None\" cannot be assigned to parameter \"start_time\" of type \"datetime\" in function \"_create_step\"\n  Type \"Unknown | datetime | None\" is not assignable to type \"datetime\"\n    \"None\" is not assignable to \"datetime\"",
	"source": "basedpyright",
	"startLineNumber": 106,
	"startColumn": 21,
	"endLineNumber": 106,
	"endColumn": 31
},{
	"resource": "/e:/grid/archival/python_unclear/Python/src/ide_recorder/uploader.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportGeneralTypeIssues",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportGeneralTypeIssues"
		}
	},
	"severity": 8,
	"message": "Expected class but received \"(obj: object, /) -> TypeIs[(...) -> object]\"",
	"source": "basedpyright",
	"startLineNumber": 102,
	"startColumn": 31,
	"endLineNumber": 102,
	"endColumn": 39
},{
	"resource": "/e:/grid/archival/python_unclear/Python/src/ide_recorder/uploader.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportGeneralTypeIssues",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportGeneralTypeIssues"
		}
	},
	"severity": 8,
	"message": "Expected class but received \"(obj: object, /) -> TypeIs[(...) -> object]\"",
	"source": "basedpyright",
	"startLineNumber": 148,
	"startColumn": 31,
	"endLineNumber": 148,
	"endColumn": 39
},{
	"resource": "/e:/grid/archival/python_unclear/Python/src/main.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.dice\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 6,
	"startColumn": 6,
	"endLineNumber": 6,
	"endColumn": 19
},{
	"resource": "/e:/grid/archival/python_unclear/Python/src/main.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.logger\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 6,
	"endLineNumber": 7,
	"endColumn": 21
},{
	"resource": "/e:/grid/archival/python_unclear/Python/tests/conftest.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.dice\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 11,
	"startColumn": 6,
	"endLineNumber": 11,
	"endColumn": 19
},{
	"resource": "/e:/grid/archival/python_unclear/Python/tests/test_dice.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.dice\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 5,
	"startColumn": 6,
	"endLineNumber": 5,
	"endColumn": 19
},{
	"resource": "/e:/grid/archival/python_unclear/Python/youtube_video_simulation.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"None\" is not assignable to declared type \"List[str]\"\n  \"None\" is not assignable to \"List[str]\"",
	"source": "basedpyright",
	"startLineNumber": 70,
	"startColumn": 31,
	"endLineNumber": 70,
	"endColumn": 35
},{
	"resource": "/e:/grid/archival/python_unclear/Python/youtube_video_simulation.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"None\" cannot be assigned to parameter of type \"int\"\n  \"None\" is not assignable to \"int\"",
	"source": "basedpyright",
	"startLineNumber": 217,
	"startColumn": 61,
	"endLineNumber": 217,
	"endColumn": 65
},{
	"resource": "/e:/grid/archival/transformer_root/transformer/main.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"prometheus_client\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 8,
	"startColumn": 8,
	"endLineNumber": 8,
	"endColumn": 25
},{
	"resource": "/e:/grid/archival/transformer_root/transformer/main.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"azure.storage.blob\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 9,
	"startColumn": 6,
	"endLineNumber": 9,
	"endColumn": 24
},{
	"resource": "/e:/grid/archival/transformer_root/transformer/main.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"confluent_kafka\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 10,
	"startColumn": 6,
	"endLineNumber": 10,
	"endColumn": 21
},{
	"resource": "/e:/grid/archival/transformer_root/transformer/main.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"get_blob_client\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 196,
	"startColumn": 43,
	"endLineNumber": 196,
	"endColumn": 58
},{
	"resource": "/e:/grid/async_stress_harness.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"List[float]\" cannot be assigned to parameter \"value\" of type \"Dict[str, Any]\" in function \"__setitem__\"\n  \"List[float]\" is not assignable to \"Dict[str, Any]\"",
	"source": "basedpyright",
	"startLineNumber": 88,
	"startColumn": 9,
	"endLineNumber": 88,
	"endColumn": 33
},{
	"resource": "/e:/grid/datakit/artifacts/AGENTS/backend/server.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Invalid character \"\\ufffd\" in token",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 1,
	"endLineNumber": 1,
	"endColumn": 23
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportReturnType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportReturnType"
		}
	},
	"severity": 8,
	"message": "Type \"str | Literal[True] | None\" is not assignable to return type \"bool\"\n  Type \"str | Literal[True] | None\" is not assignable to type \"bool\"\n    \"str\" is not assignable to \"bool\"",
	"source": "basedpyright",
	"startLineNumber": 122,
	"startColumn": 20,
	"endLineNumber": 122,
	"endColumn": 86
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"name\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 215,
	"startColumn": 41,
	"endLineNumber": 215,
	"endColumn": 45
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"description\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 216,
	"startColumn": 26,
	"endLineNumber": 216,
	"endColumn": 37
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"description\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 216,
	"startColumn": 71,
	"endLineNumber": 216,
	"endColumn": 82
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"description\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 216,
	"startColumn": 107,
	"endLineNumber": 216,
	"endColumn": 118
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"introduction\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 221,
	"startColumn": 25,
	"endLineNumber": 221,
	"endColumn": 37
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"introduction\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 223,
	"startColumn": 32,
	"endLineNumber": 223,
	"endColumn": 44
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"name\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 226,
	"startColumn": 70,
	"endLineNumber": 226,
	"endColumn": 74
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"modules\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 232,
	"startColumn": 58,
	"endLineNumber": 232,
	"endColumn": 65
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"challenges\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 233,
	"startColumn": 60,
	"endLineNumber": 233,
	"endColumn": 70
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"fun_facts\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 234,
	"startColumn": 63,
	"endLineNumber": 234,
	"endColumn": 72
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"name\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 241,
	"startColumn": 41,
	"endLineNumber": 241,
	"endColumn": 45
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"modules\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 245,
	"startColumn": 81,
	"endLineNumber": 245,
	"endColumn": 88
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"modules\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 295,
	"startColumn": 29,
	"endLineNumber": 295,
	"endColumn": 36
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"modules\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 303,
	"startColumn": 46,
	"endLineNumber": 303,
	"endColumn": 53
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"modules\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 304,
	"startColumn": 35,
	"endLineNumber": 304,
	"endColumn": 42
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"modules\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 307,
	"startColumn": 87,
	"endLineNumber": 307,
	"endColumn": 94
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"modules\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 346,
	"startColumn": 77,
	"endLineNumber": 346,
	"endColumn": 84
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"modules\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 348,
	"startColumn": 44,
	"endLineNumber": 348,
	"endColumn": 51
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"topic_type\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 354,
	"startColumn": 25,
	"endLineNumber": 354,
	"endColumn": 35
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"data\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 361,
	"startColumn": 29,
	"endLineNumber": 361,
	"endColumn": 33
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"data\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 413,
	"startColumn": 29,
	"endLineNumber": 413,
	"endColumn": 33
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"data\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 680,
	"startColumn": 29,
	"endLineNumber": 680,
	"endColumn": 33
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"data\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 721,
	"startColumn": 29,
	"endLineNumber": 721,
	"endColumn": 33
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"challenges\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 824,
	"startColumn": 29,
	"endLineNumber": 824,
	"endColumn": 39
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"challenges\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 830,
	"startColumn": 57,
	"endLineNumber": 830,
	"endColumn": 67
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"challenges\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 832,
	"startColumn": 52,
	"endLineNumber": 832,
	"endColumn": 62
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"challenges\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 844,
	"startColumn": 48,
	"endLineNumber": 844,
	"endColumn": 58
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"challenges\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 845,
	"startColumn": 54,
	"endLineNumber": 845,
	"endColumn": 64
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"data\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 851,
	"startColumn": 29,
	"endLineNumber": 851,
	"endColumn": 33
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"fun_facts\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 915,
	"startColumn": 29,
	"endLineNumber": 915,
	"endColumn": 38
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"fun_facts\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 921,
	"startColumn": 47,
	"endLineNumber": 921,
	"endColumn": 56
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"summary\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 973,
	"startColumn": 28,
	"endLineNumber": 973,
	"endColumn": 35
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"source_path\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 976,
	"startColumn": 25,
	"endLineNumber": 976,
	"endColumn": 36
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"source_path\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 977,
	"startColumn": 43,
	"endLineNumber": 977,
	"endColumn": 54
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"author\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 980,
	"startColumn": 39,
	"endLineNumber": 980,
	"endColumn": 45
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"version\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 981,
	"startColumn": 40,
	"endLineNumber": 981,
	"endColumn": 47
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"topic_type\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 982,
	"startColumn": 37,
	"endLineNumber": 982,
	"endColumn": 47
},{
	"resource": "/e:/grid/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"name\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 1009,
	"startColumn": 75,
	"endLineNumber": 1009,
	"endColumn": 79
},{
	"resource": "/e:/grid/datakit/Hogwarts/great_hall/mistral_agent.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"agents.function_definitions\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 32,
	"startColumn": 10,
	"endLineNumber": 32,
	"endColumn": 37
},{
	"resource": "/e:/grid/datakit/Hogwarts/great_hall/mistral_agent.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \".agents.function_definitions\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 39,
	"startColumn": 10,
	"endLineNumber": 39,
	"endColumn": 38
},{
	"resource": "/e:/grid/datakit/Hogwarts/great_hall/mistral_agent.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"list[dict[str, str]]\" cannot be assigned to parameter \"messages\" of type \"List[Messages] | List[MessagesTypedDict]\" in function \"complete\"\n  Type \"list[dict[str, str]]\" is not assignable to type \"List[Messages] | List[MessagesTypedDict]\"\n    \"list[dict[str, str]]\" is not assignable to \"List[Messages]\"\n      Type parameter \"_T@list\" is invariant, but \"dict[str, str]\" is not the same as \"Messages\"\n      Consider switching from \"list\" to \"Sequence\" which is covariant\n    \"list[dict[str, str]]\" is not assignable to \"List[MessagesTypedDict]\"\n      Type parameter \"_T@list\" is invariant, but \"dict[str, str]\" is not the same as \"MessagesTypedDict\"\n      Consider switching from \"list\" to \"Sequence\" which is covariant",
	"source": "basedpyright",
	"startLineNumber": 138,
	"startColumn": 22,
	"endLineNumber": 138,
	"endColumn": 30
},{
	"resource": "/e:/grid/datakit/Hogwarts/great_hall/mistral_agent.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"continue_conversation\" for class \"Conversations\"\n  Attribute \"continue_conversation\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 162,
	"startColumn": 51,
	"endLineNumber": 162,
	"endColumn": 72
},{
	"resource": "/e:/grid/datakit/Hogwarts/great_hall/run_recommended_stream.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportReturnType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportReturnType"
		}
	},
	"severity": 8,
	"message": "Type \"tuple[Path, Path, Path, Path, Path]\" is not assignable to return type \"tuple[Path, Path, Path, Path]\"\n  \"tuple[Path, Path, Path, Path, Path]\" is not assignable to \"tuple[Path, Path, Path, Path]\"\n    Tuple size mismatch; expected 4 but received 5",
	"source": "basedpyright",
	"startLineNumber": 47,
	"startColumn": 12,
	"endLineNumber": 47,
	"endColumn": 78
},{
	"resource": "/e:/grid/datakit/Hogwarts/great_hall/run_recommended_stream.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Expression with type \"tuple[Path, Path, Path, Path]\" cannot be assigned to target tuple\n  Type \"tuple[Path, Path, Path, Path]\" is incompatible with target tuple\n    Tuple size mismatch; expected 5 but received 4",
	"source": "basedpyright",
	"startLineNumber": 117,
	"startColumn": 5,
	"endLineNumber": 117,
	"endColumn": 50
},{
	"resource": "/e:/grid/datakit/Hogwarts/great_hall/table/great_hall_table.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"Any | None\" cannot be assigned to parameter \"speaker_id\" of type \"str\" in function \"_resolve_speaker\"\n  Type \"Any | None\" is not assignable to type \"str\"\n    \"None\" is not assignable to \"str\"",
	"source": "basedpyright",
	"startLineNumber": 140,
	"startColumn": 88,
	"endLineNumber": 140,
	"endColumn": 105
},{
	"resource": "/e:/grid/datakit/Hogwarts/grid_bridge.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportReturnType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportReturnType"
		}
	},
	"severity": 8,
	"message": "Type \"dict[str, Any] | None\" is not assignable to return type \"dict[str, Any]\"\n  Type \"dict[str, Any] | None\" is not assignable to type \"dict[str, Any]\"\n    \"None\" is not assignable to \"dict[str, Any]\"",
	"source": "basedpyright",
	"startLineNumber": 813,
	"startColumn": 16,
	"endLineNumber": 813,
	"endColumn": 31
},{
	"resource": "/e:/grid/datakit/Hogwarts/spellbook_api.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"google_auth_oauthlib.flow\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 44,
	"startColumn": 10,
	"endLineNumber": 44,
	"endColumn": 35
},{
	"resource": "/e:/grid/datakit/Hogwarts/spellbook_api.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"googleapiclient.discovery\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 45,
	"startColumn": 10,
	"endLineNumber": 45,
	"endColumn": 35
},{
	"resource": "/e:/grid/datakit/scripts/chord_generator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"Path\" is not assignable to declared type \"str | None\"\n  Type \"Path\" is not assignable to type \"str | None\"\n    \"Path\" is not assignable to \"str\"\n    \"Path\" is not assignable to \"None\"",
	"source": "basedpyright",
	"startLineNumber": 70,
	"startColumn": 25,
	"endLineNumber": 70,
	"endColumn": 72
},{
	"resource": "/e:/grid/datakit/scripts/chord_generator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportCallIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportCallIssue"
		}
	},
	"severity": 8,
	"message": "No overloads for \"open\" match the provided arguments",
	"source": "basedpyright",
	"startLineNumber": 73,
	"startColumn": 18,
	"endLineNumber": 73,
	"endColumn": 56,
	"relatedInformation": [
		{
			"startLineNumber": 5621,
			"startColumn": 5,
			"endLineNumber": 5621,
			"endColumn": 9,
			"message": "Overload 7 is the closest match",
			"resource": "/c:/Users/irfan/.cursor/extensions/anysphere.cursorpyright-1.0.10/dist/typeshed-fallback/stdlib/builtins.pyi"
		}
	]
},{
	"resource": "/e:/grid/datakit/scripts/chord_generator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"str | None\" cannot be assigned to parameter \"file\" of type \"FileDescriptorOrPath\" in function \"open\"\n  Type \"str | None\" is not assignable to type \"FileDescriptorOrPath\"\n    Type \"None\" is not assignable to type \"FileDescriptorOrPath\"\n      \"None\" is not assignable to \"int\"\n      \"None\" is not assignable to \"str\"\n      \"None\" is not assignable to \"bytes\"\n      \"None\" is incompatible with protocol \"PathLike[str]\"\n        \"__fspath__\" is not present\n      \"None\" is incompatible with protocol \"PathLike[bytes]\"\n  ...",
	"source": "basedpyright",
	"startLineNumber": 73,
	"startColumn": 23,
	"endLineNumber": 73,
	"endColumn": 32
},{
	"resource": "/e:/grid/datakit/scripts/openai_smoketest.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"object\" is not assignable to declared type \"dict[Unknown, Unknown] | None\"\n  Type \"object\" is not assignable to type \"dict[Unknown, Unknown] | None\"\n    \"object\" is not assignable to \"dict[Unknown, Unknown]\"\n    \"object\" is not assignable to \"None\"",
	"source": "basedpyright",
	"startLineNumber": 87,
	"startColumn": 29,
	"endLineNumber": 87,
	"endColumn": 33
},{
	"resource": "/e:/grid/datakit/scripts/similarity_pie.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Expression with type \"tuple[list[Wedge], list[Text]] | tuple[list[Wedge], list[Text], list[Text]]\" cannot be assigned to target tuple\n  Type \"tuple[list[Wedge], list[Text]]\" is incompatible with target tuple\n    Tuple size mismatch; expected 3 but received 2",
	"source": "basedpyright",
	"startLineNumber": 126,
	"startColumn": 5,
	"endLineNumber": 126,
	"endColumn": 29
},{
	"resource": "/e:/grid/datakit/tests/test_story_eq.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"story_eq.config\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 16,
	"startColumn": 10,
	"endLineNumber": 16,
	"endColumn": 25
},{
	"resource": "/e:/grid/datakit/tests/test_story_eq.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"story_eq.errors\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 17,
	"startColumn": 10,
	"endLineNumber": 17,
	"endColumn": 25
},{
	"resource": "/e:/grid/datakit/tests/test_story_eq.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"story_eq.models\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 18,
	"startColumn": 10,
	"endLineNumber": 18,
	"endColumn": 25
},{
	"resource": "/e:/grid/datakit/tests/test_story_eq.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"story_eq.parser\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 19,
	"startColumn": 10,
	"endLineNumber": 19,
	"endColumn": 25
},{
	"resource": "/e:/grid/datakit/tests/test_story_eq.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"story_eq.validation\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 20,
	"startColumn": 10,
	"endLineNumber": 20,
	"endColumn": 29
},{
	"resource": "/e:/grid/datakit/tests/test_story_eq.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"story_eq.ui\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 324,
	"startColumn": 14,
	"endLineNumber": 324,
	"endColumn": 25
},{
	"resource": "/e:/grid/datakit/tests/test_story_eq.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"story_eq.ui\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 330,
	"startColumn": 14,
	"endLineNumber": 330,
	"endColumn": 25
},{
	"resource": "/e:/grid/datakit/tests/test_story_eq.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"story_eq.ui\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 336,
	"startColumn": 14,
	"endLineNumber": 336,
	"endColumn": 25
},{
	"resource": "/e:/grid/datakit/tool/semantic_grep.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"sentence_transformers\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 100,
	"startColumn": 14,
	"endLineNumber": 100,
	"endColumn": 35
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"manim\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 10,
	"startColumn": 6,
	"endLineNumber": 10,
	"endColumn": 11
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Scene\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 13,
	"startColumn": 22,
	"endLineNumber": 13,
	"endColumn": 27
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Circle\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 20,
	"startColumn": 18,
	"endLineNumber": 20,
	"endColumn": 24
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"BLUE\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 20,
	"startColumn": 41,
	"endLineNumber": 20,
	"endColumn": 45
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Create\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 21,
	"startColumn": 19,
	"endLineNumber": 21,
	"endColumn": 25
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"VGroup\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 25,
	"startColumn": 22,
	"endLineNumber": 25,
	"endColumn": 28
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 27,
	"startColumn": 30,
	"endLineNumber": 27,
	"endColumn": 32
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 27,
	"startColumn": 47,
	"endLineNumber": 27,
	"endColumn": 49
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Text\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 28,
	"startColumn": 21,
	"endLineNumber": 28,
	"endColumn": 25
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Write\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 31,
	"startColumn": 19,
	"endLineNumber": 31,
	"endColumn": 24
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 36,
	"startColumn": 36,
	"endLineNumber": 36,
	"endColumn": 38
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 36,
	"startColumn": 53,
	"endLineNumber": 36,
	"endColumn": 55
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 37,
	"startColumn": 53,
	"endLineNumber": 37,
	"endColumn": 55
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 37,
	"startColumn": 70,
	"endLineNumber": 37,
	"endColumn": 72
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Arrow\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 40,
	"startColumn": 21,
	"endLineNumber": 40,
	"endColumn": 26
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"YELLOW\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 43,
	"startColumn": 23,
	"endLineNumber": 43,
	"endColumn": 29
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Text\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 49,
	"startColumn": 32,
	"endLineNumber": 49,
	"endColumn": 36
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"UP\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 49,
	"startColumn": 83,
	"endLineNumber": 49,
	"endColumn": 85
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"GrowArrow\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 52,
	"startColumn": 17,
	"endLineNumber": 52,
	"endColumn": 26
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Write\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 53,
	"startColumn": 17,
	"endLineNumber": 53,
	"endColumn": 22
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"FadeOut\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 57,
	"startColumn": 17,
	"endLineNumber": 57,
	"endColumn": 24
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"FadeOut\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 58,
	"startColumn": 17,
	"endLineNumber": 58,
	"endColumn": 24
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Text\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 62,
	"startColumn": 21,
	"endLineNumber": 62,
	"endColumn": 25
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"UP\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 63,
	"startColumn": 27,
	"endLineNumber": 63,
	"endColumn": 29
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Write\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 64,
	"startColumn": 19,
	"endLineNumber": 64,
	"endColumn": 24
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"BulletedList\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 67,
	"startColumn": 27,
	"endLineNumber": 67,
	"endColumn": 39
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"DOWN\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 74,
	"startColumn": 44,
	"endLineNumber": 74,
	"endColumn": 48
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Write\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 75,
	"startColumn": 19,
	"endLineNumber": 75,
	"endColumn": 24
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"FadeOut\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 80,
	"startColumn": 13,
	"endLineNumber": 80,
	"endColumn": 20
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"FadeOut\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 81,
	"startColumn": 13,
	"endLineNumber": 81,
	"endColumn": 20
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"FadeOut\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 82,
	"startColumn": 13,
	"endLineNumber": 82,
	"endColumn": 20
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"FadeOut\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 83,
	"startColumn": 13,
	"endLineNumber": 83,
	"endColumn": 20
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Text\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 88,
	"startColumn": 23,
	"endLineNumber": 88,
	"endColumn": 27
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"UP\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 89,
	"startColumn": 29,
	"endLineNumber": 89,
	"endColumn": 31
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Write\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 90,
	"startColumn": 19,
	"endLineNumber": 90,
	"endColumn": 24
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"BulletedList\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 93,
	"startColumn": 29,
	"endLineNumber": 93,
	"endColumn": 41
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"DOWN\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 100,
	"startColumn": 48,
	"endLineNumber": 100,
	"endColumn": 52
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Write\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 101,
	"startColumn": 19,
	"endLineNumber": 101,
	"endColumn": 24
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"FadeOut\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 106,
	"startColumn": 13,
	"endLineNumber": 106,
	"endColumn": 20
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"FadeOut\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 107,
	"startColumn": 13,
	"endLineNumber": 107,
	"endColumn": 20
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Circle\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 112,
	"startColumn": 18,
	"endLineNumber": 112,
	"endColumn": 24
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"BLUE\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 112,
	"startColumn": 41,
	"endLineNumber": 112,
	"endColumn": 45
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Create\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 113,
	"startColumn": 19,
	"endLineNumber": 113,
	"endColumn": 25
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"VGroup\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 115,
	"startColumn": 22,
	"endLineNumber": 115,
	"endColumn": 28
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 117,
	"startColumn": 30,
	"endLineNumber": 117,
	"endColumn": 32
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 117,
	"startColumn": 47,
	"endLineNumber": 117,
	"endColumn": 49
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Text\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 118,
	"startColumn": 21,
	"endLineNumber": 118,
	"endColumn": 25
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Write\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 121,
	"startColumn": 19,
	"endLineNumber": 121,
	"endColumn": 24
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"VGroup\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 126,
	"startColumn": 30,
	"endLineNumber": 126,
	"endColumn": 36
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 130,
	"startColumn": 34,
	"endLineNumber": 130,
	"endColumn": 36
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 130,
	"startColumn": 51,
	"endLineNumber": 130,
	"endColumn": 53
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Dot\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 131,
	"startColumn": 19,
	"endLineNumber": 131,
	"endColumn": 22
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"RED\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 131,
	"startColumn": 59,
	"endLineNumber": 131,
	"endColumn": 62
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Text\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 132,
	"startColumn": 21,
	"endLineNumber": 132,
	"endColumn": 25
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"RED\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 132,
	"startColumn": 51,
	"endLineNumber": 132,
	"endColumn": 54
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"UP\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 132,
	"startColumn": 69,
	"endLineNumber": 132,
	"endColumn": 71
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"VGroup\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 133,
	"startColumn": 36,
	"endLineNumber": 133,
	"endColumn": 42
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"FadeIn\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 137,
	"startColumn": 17,
	"endLineNumber": 137,
	"endColumn": 23
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Write\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 138,
	"startColumn": 17,
	"endLineNumber": 138,
	"endColumn": 22
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 149,
	"startColumn": 50,
	"endLineNumber": 149,
	"endColumn": 52
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 149,
	"startColumn": 67,
	"endLineNumber": 149,
	"endColumn": 69
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 150,
	"startColumn": 46,
	"endLineNumber": 150,
	"endColumn": 48
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 150,
	"startColumn": 63,
	"endLineNumber": 150,
	"endColumn": 65
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Arrow\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 152,
	"startColumn": 25,
	"endLineNumber": 152,
	"endColumn": 30
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"GREEN\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 155,
	"startColumn": 27,
	"endLineNumber": 155,
	"endColumn": 32
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"GrowArrow\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 159,
	"startColumn": 27,
	"endLineNumber": 159,
	"endColumn": 36
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"FadeOut\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 161,
	"startColumn": 27,
	"endLineNumber": 161,
	"endColumn": 34
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Text\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 164,
	"startColumn": 25,
	"endLineNumber": 164,
	"endColumn": 29
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"DOWN\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 165,
	"startColumn": 31,
	"endLineNumber": 165,
	"endColumn": 35
},{
	"resource": "/e:/grid/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Write\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 166,
	"startColumn": 19,
	"endLineNumber": 166,
	"endColumn": 24
},{
	"resource": "/e:/grid/datakit/visualizations/drive-index-vad/tools/locus_of_control_demo.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"workspace.dials_and_knobs\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 18,
	"startColumn": 6,
	"endLineNumber": 18,
	"endColumn": 31
},{
	"resource": "/e:/grid/datakit/visualizations/drive-index-vad/tools/locus_of_control_demo.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"core.models\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 19,
	"startColumn": 6,
	"endLineNumber": 19,
	"endColumn": 17
},{
	"resource": "/e:/grid/datakit/visualizations/interactive/plotly_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"plotly.graph_objects\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 33,
	"startColumn": 12,
	"endLineNumber": 33,
	"endColumn": 32
},{
	"resource": "/e:/grid/datakit/visualizations/interactive/plotly_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"plotly.graph_objects\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 50,
	"startColumn": 16,
	"endLineNumber": 50,
	"endColumn": 36
},{
	"resource": "/e:/grid/datakit/visualizations/interactive/plotly_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingModuleSource",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingModuleSource"
		}
	},
	"severity": 4,
	"message": "Import \"networkx\" could not be resolved from source",
	"source": "basedpyright",
	"startLineNumber": 32,
	"startColumn": 12,
	"endLineNumber": 32,
	"endColumn": 20
},{
	"resource": "/e:/grid/datakit/visualizations/interactive/plotly_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingModuleSource",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingModuleSource"
		}
	},
	"severity": 4,
	"message": "Import \"networkx\" could not be resolved from source",
	"source": "basedpyright",
	"startLineNumber": 39,
	"startColumn": 16,
	"endLineNumber": 39,
	"endColumn": 24
},{
	"resource": "/e:/grid/datakit/visualizations/static/smartdecisor.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"None\" is not assignable to declared type \"List[str]\"\n  \"None\" is not assignable to \"List[str]\"",
	"source": "basedpyright",
	"startLineNumber": 46,
	"startColumn": 30,
	"endLineNumber": 46,
	"endColumn": 34
},{
	"resource": "/e:/grid/datakit/visualizations/static/smartdecisor.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"None\" is not assignable to declared type \"Dict[str, str]\"\n  \"None\" is not assignable to \"Dict[str, str]\"",
	"source": "basedpyright",
	"startLineNumber": 47,
	"startColumn": 38,
	"endLineNumber": 47,
	"endColumn": 42
},{
	"resource": "/e:/grid/datakit/visualizations/static/smartdecisor.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"None\" is not assignable to declared type \"List[str]\"\n  \"None\" is not assignable to \"List[str]\"",
	"source": "basedpyright",
	"startLineNumber": 50,
	"startColumn": 31,
	"endLineNumber": 50,
	"endColumn": 35
},{
	"resource": "/e:/grid/demos/dataset_lifecycle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"sqlalchemy\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 25,
	"startColumn": 6,
	"endLineNumber": 25,
	"endColumn": 16
},{
	"resource": "/e:/grid/demos/dataset_lifecycle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"sqlalchemy.orm\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 26,
	"startColumn": 6,
	"endLineNumber": 26,
	"endColumn": 20
},{
	"resource": "/e:/grid/demos/dataset_lifecycle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"vinci_code.core.config\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 27,
	"startColumn": 6,
	"endLineNumber": 27,
	"endColumn": 28
},{
	"resource": "/e:/grid/demos/dataset_lifecycle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"vinci_code.database.models\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 28,
	"startColumn": 6,
	"endLineNumber": 28,
	"endColumn": 32
},{
	"resource": "/e:/grid/demos/dataset_lifecycle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"vinci_code.database.models_gfashion\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 29,
	"startColumn": 6,
	"endLineNumber": 29,
	"endColumn": 41
},{
	"resource": "/e:/grid/demos/dataset_lifecycle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"vinci_code.database.session\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 30,
	"startColumn": 6,
	"endLineNumber": 30,
	"endColumn": 33
},{
	"resource": "/e:/grid/examples/grid_workflow_demo.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.grid.core.engine\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 19,
	"startColumn": 6,
	"endLineNumber": 19,
	"endColumn": 31
},{
	"resource": "/e:/grid/examples/grid_workflow_demo.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.grid.core.fear\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 20,
	"startColumn": 6,
	"endLineNumber": 20,
	"endColumn": 29
},{
	"resource": "/e:/grid/examples/grid_workflow_demo.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.grid.core.temporal\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 21,
	"startColumn": 6,
	"endLineNumber": 21,
	"endColumn": 33
},{
	"resource": "/e:/grid/examples/grid_workflow_demo.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.grid.pattern.engine\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 22,
	"startColumn": 6,
	"endLineNumber": 22,
	"endColumn": 34
},{
	"resource": "/e:/grid/examples/quantum_optimization_demo.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.services.quantum_utils\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 17,
	"startColumn": 6,
	"endLineNumber": 17,
	"endColumn": 37
},{
	"resource": "/e:/grid/examples/translator_assistant_demo.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"services.translator_assistant\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 11,
	"startColumn": 6,
	"endLineNumber": 11,
	"endColumn": 35
},{
	"resource": "/e:/grid/examples/translator_demo.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"grid.services.translator_assistant.service\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 12,
	"startColumn": 6,
	"endLineNumber": 12,
	"endColumn": 48
},{
	"resource": "/e:/grid/grid/interfaces/sensory.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"tolist\" for class \"list[int]\"\n  Attribute \"tolist\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 54,
	"startColumn": 39,
	"endLineNumber": 54,
	"endColumn": 45
},{
	"resource": "/e:/grid/grid/organization/org_manager.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"dict[str, list[str] | bool | None]\" cannot be assigned to parameter \"settings\" of type \"OrganizationSettings\" in function \"__init__\"",
	"source": "basedpyright",
	"startLineNumber": 29,
	"startColumn": 22,
	"endLineNumber": 34,
	"endColumn": 14
},{
	"resource": "/e:/grid/grid/organization/org_manager.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"dict[str, list[str] | bool | None]\" cannot be assigned to parameter \"settings\" of type \"OrganizationSettings\" in function \"__init__\"",
	"source": "basedpyright",
	"startLineNumber": 44,
	"startColumn": 22,
	"endLineNumber": 49,
	"endColumn": 14
},{
	"resource": "/e:/grid/grid/organization/org_manager.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"dict[str, list[str] | str | bool]\" cannot be assigned to parameter \"settings\" of type \"OrganizationSettings\" in function \"__init__\"",
	"source": "basedpyright",
	"startLineNumber": 59,
	"startColumn": 22,
	"endLineNumber": 64,
	"endColumn": 14
},{
	"resource": "/e:/grid/grid/quantum/locomotion.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Quantizer\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 38,
	"startColumn": 45,
	"endLineNumber": 38,
	"endColumn": 54
},{
	"resource": "/e:/grid/grid/skills/patterns_detect_entities.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"application.mothership.ner_service\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 85,
	"startColumn": 18,
	"endLineNumber": 85,
	"endColumn": 52
},{
	"resource": "/e:/grid/grid/tracing/trace_manager.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"TraceStore\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 14,
	"startColumn": 41,
	"endLineNumber": 14,
	"endColumn": 51
},{
	"resource": "/e:/grid/grid/tracing/trace_manager.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportCallIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportCallIssue"
		}
	},
	"severity": 8,
	"message": "No parameter named \"error_traceback\"",
	"source": "basedpyright",
	"startLineNumber": 166,
	"startColumn": 57,
	"endLineNumber": 166,
	"endColumn": 72
},{
	"resource": "/e:/grid/infra/cloud/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"aiohttp\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 27,
	"startColumn": 12,
	"endLineNumber": 27,
	"endColumn": 19
},{
	"resource": "/e:/grid/infra/cloud/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"request\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 476,
	"startColumn": 42,
	"endLineNumber": 476,
	"endColumn": 49
},{
	"resource": "/e:/grid/infra/cloud/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"request\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 486,
	"startColumn": 36,
	"endLineNumber": 486,
	"endColumn": 43
},{
	"resource": "/e:/grid/infra/cloud/gemini_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"google.generativeai\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 45,
	"startColumn": 12,
	"endLineNumber": 45,
	"endColumn": 31
},{
	"resource": "/e:/grid/infra/cloud/gemini_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportGeneralTypeIssues",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportGeneralTypeIssues"
		}
	},
	"severity": 8,
	"message": "\"object*\" is not awaitable\n  \"object*\" is incompatible with protocol \"Awaitable[_T_co@Awaitable]\"\n    \"__await__\" is not present",
	"source": "basedpyright",
	"startLineNumber": 142,
	"startColumn": 30,
	"endLineNumber": 142,
	"endColumn": 57
},{
	"resource": "/e:/grid/infra/cloud/gemini_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportInvalidTypeForm",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportInvalidTypeForm"
		}
	},
	"severity": 8,
	"message": "Variable not allowed in type expression",
	"source": "basedpyright",
	"startLineNumber": 216,
	"startColumn": 37,
	"endLineNumber": 216,
	"endColumn": 42
},{
	"resource": "/e:/grid/infra/cloud/gemini_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"ConnectError\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 362,
	"startColumn": 22,
	"endLineNumber": 362,
	"endColumn": 34
},{
	"resource": "/e:/grid/infra/cloud/gemini_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"TimeoutException\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 364,
	"startColumn": 22,
	"endLineNumber": 364,
	"endColumn": 38
},{
	"resource": "/e:/grid/infra/cloud/gemini_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"ConnectError\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 426,
	"startColumn": 22,
	"endLineNumber": 426,
	"endColumn": 34
},{
	"resource": "/e:/grid/infra/cloud/gemini_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"TimeoutException\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 428,
	"startColumn": 22,
	"endLineNumber": 428,
	"endColumn": 38
},{
	"resource": "/e:/grid/infra/cloud/gemini_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"ConnectError\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 492,
	"startColumn": 22,
	"endLineNumber": 492,
	"endColumn": 34
},{
	"resource": "/e:/grid/infra/cloud/test_gemini_integration.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOperatorIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOperatorIssue"
		}
	},
	"severity": 8,
	"message": "Operator \"in\" not supported for types \"Literal['[MOCK]']\" and \"str | None\"\n  Operator \"in\" not supported for types \"Literal['[MOCK]']\" and \"None\"",
	"source": "basedpyright",
	"startLineNumber": 315,
	"startColumn": 16,
	"endLineNumber": 315,
	"endColumn": 41
},{
	"resource": "/e:/grid/infra/cloud/test_gemini_integration.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOperatorIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOperatorIssue"
		}
	},
	"severity": 8,
	"message": "Operator \"in\" not supported for types \"Literal['[MOCK]']\" and \"str | None\"\n  Operator \"in\" not supported for types \"Literal['[MOCK]']\" and \"None\"",
	"source": "basedpyright",
	"startLineNumber": 325,
	"startColumn": 16,
	"endLineNumber": 325,
	"endColumn": 41
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/dependencies.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportReturnType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportReturnType"
		}
	},
	"severity": 8,
	"message": "Type \"CoroutineType[Any, Any, Dict[str, Any]]\" is not assignable to return type \"Dict[str, Any]\"\n  \"CoroutineType[Any, Any, Dict[str, Any]]\" is not assignable to \"Dict[str, Any]\"",
	"source": "basedpyright",
	"startLineNumber": 322,
	"startColumn": 12,
	"endLineNumber": 322,
	"endColumn": 45
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/dependencies.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportReturnType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportReturnType"
		}
	},
	"severity": 8,
	"message": "Type \"CoroutineType[Any, Any, Dict[str, Any]]\" is not assignable to return type \"Dict[str, Any]\"\n  \"CoroutineType[Any, Any, Dict[str, Any]]\" is not assignable to \"Dict[str, Any]\"",
	"source": "basedpyright",
	"startLineNumber": 327,
	"startColumn": 12,
	"endLineNumber": 327,
	"endColumn": 45
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/dependencies.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportReturnType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportReturnType"
		}
	},
	"severity": 8,
	"message": "Type \"Session\" is not assignable to return type \"Session | None\"\n  Type \"Session\" is not assignable to type \"Session | None\"\n    \"light_of_the_seven.application.mothership.models.Session\" is not assignable to \"light_of_the_seven.application.mothership.models.cockpit.Session\"\n    \"Session\" is not assignable to \"None\"",
	"source": "basedpyright",
	"startLineNumber": 377,
	"startColumn": 16,
	"endLineNumber": 377,
	"endColumn": 56
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/dependencies.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportCallIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportCallIssue"
		}
	},
	"severity": 8,
	"message": "Object of type \"bool\" is not callable\n  Attribute \"__call__\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 407,
	"startColumn": 12,
	"endLineNumber": 407,
	"endColumn": 31
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/main.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"(request: Request, exc: MothershipError) -> CoroutineType[Any, Any, JSONResponse]\" cannot be assigned to parameter \"handler\" of type \"ExceptionHandler\" in function \"add_exception_handler\"\n  Type \"(request: Request, exc: MothershipError) -> CoroutineType[Any, Any, JSONResponse]\" is not assignable to type \"ExceptionHandler\"\n    Type \"(request: Request, exc: MothershipError) -> CoroutineType[Any, Any, JSONResponse]\" is not assignable to type \"HTTPExceptionHandler\"\n      Parameter 2: type \"Exception\" is incompatible with type \"MothershipError\"\n        \"Exception\" is not assignable to \"MothershipError\"\n    Type \"(request: Request, exc: MothershipError) -> CoroutineType[Any, Any, JSONResponse]\" is not assignable to type \"WebSocketExceptionHandler\"\n      Parameter 1: type \"WebSocket\" is incompatible with type \"Request\"\n        \"WebSocket\" is not assignable to \"Request\"\n      Parameter 2: type \"Exception\" is incompatible with type \"MothershipError\"\n  ...",
	"source": "basedpyright",
	"startLineNumber": 337,
	"startColumn": 48,
	"endLineNumber": 337,
	"endColumn": 72
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/main.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"(request: Request, exc: HTTPException) -> CoroutineType[Any, Any, JSONResponse]\" cannot be assigned to parameter \"handler\" of type \"ExceptionHandler\" in function \"add_exception_handler\"\n  Type \"(request: Request, exc: HTTPException) -> CoroutineType[Any, Any, JSONResponse]\" is not assignable to type \"ExceptionHandler\"\n    Type \"(request: Request, exc: HTTPException) -> CoroutineType[Any, Any, JSONResponse]\" is not assignable to type \"HTTPExceptionHandler\"\n      Parameter 2: type \"Exception\" is incompatible with type \"HTTPException\"\n        \"Exception\" is not assignable to \"HTTPException\"\n    Type \"(request: Request, exc: HTTPException) -> CoroutineType[Any, Any, JSONResponse]\" is not assignable to type \"WebSocketExceptionHandler\"\n      Parameter 1: type \"WebSocket\" is incompatible with type \"Request\"\n        \"WebSocket\" is not assignable to \"Request\"\n      Parameter 2: type \"Exception\" is incompatible with type \"HTTPException\"\n  ...",
	"source": "basedpyright",
	"startLineNumber": 338,
	"startColumn": 46,
	"endLineNumber": 338,
	"endColumn": 68
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/main.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"(request: Request, exc: RequestValidationError) -> CoroutineType[Any, Any, JSONResponse]\" cannot be assigned to parameter \"handler\" of type \"ExceptionHandler\" in function \"add_exception_handler\"\n  Type \"(request: Request, exc: RequestValidationError) -> CoroutineType[Any, Any, JSONResponse]\" is not assignable to type \"ExceptionHandler\"\n    Type \"(request: Request, exc: RequestValidationError) -> CoroutineType[Any, Any, JSONResponse]\" is not assignable to type \"HTTPExceptionHandler\"\n      Parameter 2: type \"Exception\" is incompatible with type \"RequestValidationError\"\n        \"Exception\" is not assignable to \"RequestValidationError\"\n    Type \"(request: Request, exc: RequestValidationError) -> CoroutineType[Any, Any, JSONResponse]\" is not assignable to type \"WebSocketExceptionHandler\"\n      Parameter 1: type \"WebSocket\" is incompatible with type \"Request\"\n        \"WebSocket\" is not assignable to \"Request\"\n      Parameter 2: type \"Exception\" is incompatible with type \"RequestValidationError\"\n  ...",
	"source": "basedpyright",
	"startLineNumber": 339,
	"startColumn": 55,
	"endLineNumber": 339,
	"endColumn": 79
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/main.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"grid.api.routers\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 382,
	"startColumn": 18,
	"endLineNumber": 382,
	"endColumn": 34
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/repositories/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"ComponentHealth\" cannot be assigned to parameter \"health\" of type \"ComponentHealth\" in function \"update_health\"\n  \"light_of_the_seven.application.mothership.models.ComponentHealth\" is not assignable to \"light_of_the_seven.application.mothership.models.cockpit.ComponentHealth\"",
	"source": "basedpyright",
	"startLineNumber": 482,
	"startColumn": 37,
	"endLineNumber": 482,
	"endColumn": 43
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/repositories/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"Literal[AlertSeverity.CRITICAL]\" cannot be assigned to parameter \"severity\" of type \"AlertSeverity\" in function \"get_by_severity\"\n  \"Literal[AlertSeverity.CRITICAL]\" is not assignable to \"AlertSeverity\"",
	"source": "basedpyright",
	"startLineNumber": 555,
	"startColumn": 43,
	"endLineNumber": 555,
	"endColumn": 65
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/repositories/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"OperationMode\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 626,
	"startColumn": 37,
	"endLineNumber": 626,
	"endColumn": 50
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/routers/cockpit.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"type | Literal['warning']\" cannot be assigned to parameter \"severity\" of type \"AlertSeverity\" in function \"create_alert\"\n  Type \"type | Literal['warning']\" is not assignable to type \"AlertSeverity\"\n    \"Literal['warning']\" is not assignable to \"AlertSeverity\"",
	"source": "basedpyright",
	"startLineNumber": 633,
	"startColumn": 18,
	"endLineNumber": 637,
	"endColumn": 10
},{
	"resource": "/e:/grid/light_of_the_seven/archival/debug/debug_articulation.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.kernel.bus\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 6,
	"endLineNumber": 1,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/archival/debug/debug_articulation.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.plugins.articulation\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 6,
	"endLineNumber": 7,
	"endColumn": 35
},{
	"resource": "/e:/grid/light_of_the_seven/archival/debug/debug_articulation2.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.kernel.bus\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 6,
	"endLineNumber": 1,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/archival/debug/debug_articulation2.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.plugins.articulation\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 6,
	"endLineNumber": 7,
	"endColumn": 35
},{
	"resource": "/e:/grid/light_of_the_seven/archival/debug/debug_articulation3.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.kernel.bus\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 6,
	"endLineNumber": 1,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/archival/debug/debug_articulation3.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.plugins.articulation\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 6,
	"endLineNumber": 7,
	"endColumn": 35
},{
	"resource": "/e:/grid/light_of_the_seven/archival/debug/debug_physics.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.kernel.bus\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 6,
	"endLineNumber": 1,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/archival/debug/debug_physics.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.plugins.physics\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 6,
	"endLineNumber": 7,
	"endColumn": 30
},{
	"resource": "/e:/grid/light_of_the_seven/archival/debug/debug_physics.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.kernel.bus\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 13,
	"startColumn": 14,
	"endLineNumber": 13,
	"endColumn": 33
},{
	"resource": "/e:/grid/light_of_the_seven/archival/python_unclear/Python/ide_recorder_cli.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.ide_recorder\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 21,
	"startColumn": 6,
	"endLineNumber": 21,
	"endColumn": 27
},{
	"resource": "/e:/grid/light_of_the_seven/archival/python_unclear/Python/ide_recorder_cli.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.ide_recorder.events\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 30,
	"startColumn": 6,
	"endLineNumber": 30,
	"endColumn": 34
},{
	"resource": "/e:/grid/light_of_the_seven/archival/python_unclear/Python/ide_recorder_cli.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.ide_recorder.narrator\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 31,
	"startColumn": 6,
	"endLineNumber": 31,
	"endColumn": 36
},{
	"resource": "/e:/grid/light_of_the_seven/archival/python_unclear/Python/ide_recorder_cli.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.ide_recorder.uploader\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 32,
	"startColumn": 6,
	"endLineNumber": 32,
	"endColumn": 36
},{
	"resource": "/e:/grid/light_of_the_seven/archival/python_unclear/Python/run_variant_simulation.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"None\" is not assignable to declared type \"List[str]\"\n  \"None\" is not assignable to \"List[str]\"",
	"source": "basedpyright",
	"startLineNumber": 49,
	"startColumn": 29,
	"endLineNumber": 49,
	"endColumn": 33
},{
	"resource": "/e:/grid/light_of_the_seven/archival/python_unclear/Python/run_variant_simulation.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"None\" cannot be assigned to parameter of type \"int\"\n  \"None\" is not assignable to \"int\"",
	"source": "basedpyright",
	"startLineNumber": 111,
	"startColumn": 52,
	"endLineNumber": 111,
	"endColumn": 56
},{
	"resource": "/e:/grid/light_of_the_seven/archival/python_unclear/Python/sora_prompt_generator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"error_patterns\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 609,
	"startColumn": 27,
	"endLineNumber": 609,
	"endColumn": 41
},{
	"resource": "/e:/grid/light_of_the_seven/archival/python_unclear/Python/sora_prompt_generator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"error_patterns\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 610,
	"startColumn": 30,
	"endLineNumber": 610,
	"endColumn": 44
},{
	"resource": "/e:/grid/light_of_the_seven/archival/python_unclear/Python/tests/conftest.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.dice\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 11,
	"startColumn": 6,
	"endLineNumber": 11,
	"endColumn": 19
},{
	"resource": "/e:/grid/light_of_the_seven/archival/python_unclear/Python/tests/test_dice.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.dice\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 5,
	"startColumn": 6,
	"endLineNumber": 5,
	"endColumn": 19
},{
	"resource": "/e:/grid/light_of_the_seven/archival/python_unclear/Python/youtube_video_simulation.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"None\" is not assignable to declared type \"List[str]\"\n  \"None\" is not assignable to \"List[str]\"",
	"source": "basedpyright",
	"startLineNumber": 70,
	"startColumn": 31,
	"endLineNumber": 70,
	"endColumn": 35
},{
	"resource": "/e:/grid/light_of_the_seven/archival/python_unclear/Python/youtube_video_simulation.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"None\" cannot be assigned to parameter of type \"int\"\n  \"None\" is not assignable to \"int\"",
	"source": "basedpyright",
	"startLineNumber": 217,
	"startColumn": 61,
	"endLineNumber": 217,
	"endColumn": 65
},{
	"resource": "/e:/grid/light_of_the_seven/archival/transformer_root/transformer/main.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"prometheus_client\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 8,
	"startColumn": 8,
	"endLineNumber": 8,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/archival/transformer_root/transformer/main.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"azure.storage.blob\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 9,
	"startColumn": 6,
	"endLineNumber": 9,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/archival/transformer_root/transformer/main.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"confluent_kafka\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 10,
	"startColumn": 6,
	"endLineNumber": 10,
	"endColumn": 21
},{
	"resource": "/e:/grid/light_of_the_seven/archival/transformer_root/transformer/main.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"get_blob_client\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 196,
	"startColumn": 43,
	"endLineNumber": 196,
	"endColumn": 58
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportReturnType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportReturnType"
		}
	},
	"severity": 8,
	"message": "Type \"str | Literal[True] | None\" is not assignable to return type \"bool\"\n  Type \"str | Literal[True] | None\" is not assignable to type \"bool\"\n    \"str\" is not assignable to \"bool\"",
	"source": "basedpyright",
	"startLineNumber": 122,
	"startColumn": 20,
	"endLineNumber": 122,
	"endColumn": 86
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"name\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 215,
	"startColumn": 41,
	"endLineNumber": 215,
	"endColumn": 45
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"description\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 216,
	"startColumn": 26,
	"endLineNumber": 216,
	"endColumn": 37
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"description\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 216,
	"startColumn": 71,
	"endLineNumber": 216,
	"endColumn": 82
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"description\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 216,
	"startColumn": 107,
	"endLineNumber": 216,
	"endColumn": 118
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"introduction\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 221,
	"startColumn": 25,
	"endLineNumber": 221,
	"endColumn": 37
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"introduction\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 223,
	"startColumn": 32,
	"endLineNumber": 223,
	"endColumn": 44
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"name\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 226,
	"startColumn": 70,
	"endLineNumber": 226,
	"endColumn": 74
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"modules\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 232,
	"startColumn": 58,
	"endLineNumber": 232,
	"endColumn": 65
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"challenges\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 233,
	"startColumn": 60,
	"endLineNumber": 233,
	"endColumn": 70
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"fun_facts\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 234,
	"startColumn": 63,
	"endLineNumber": 234,
	"endColumn": 72
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"name\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 241,
	"startColumn": 41,
	"endLineNumber": 241,
	"endColumn": 45
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"modules\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 245,
	"startColumn": 81,
	"endLineNumber": 245,
	"endColumn": 88
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"modules\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 295,
	"startColumn": 29,
	"endLineNumber": 295,
	"endColumn": 36
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"modules\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 303,
	"startColumn": 46,
	"endLineNumber": 303,
	"endColumn": 53
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"modules\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 304,
	"startColumn": 35,
	"endLineNumber": 304,
	"endColumn": 42
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"modules\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 307,
	"startColumn": 87,
	"endLineNumber": 307,
	"endColumn": 94
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"modules\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 346,
	"startColumn": 77,
	"endLineNumber": 346,
	"endColumn": 84
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"modules\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 348,
	"startColumn": 44,
	"endLineNumber": 348,
	"endColumn": 51
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"topic_type\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 354,
	"startColumn": 25,
	"endLineNumber": 354,
	"endColumn": 35
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"data\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 361,
	"startColumn": 29,
	"endLineNumber": 361,
	"endColumn": 33
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"data\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 413,
	"startColumn": 29,
	"endLineNumber": 413,
	"endColumn": 33
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"data\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 680,
	"startColumn": 29,
	"endLineNumber": 680,
	"endColumn": 33
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"data\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 721,
	"startColumn": 29,
	"endLineNumber": 721,
	"endColumn": 33
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"challenges\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 824,
	"startColumn": 29,
	"endLineNumber": 824,
	"endColumn": 39
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"challenges\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 830,
	"startColumn": 57,
	"endLineNumber": 830,
	"endColumn": 67
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"challenges\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 832,
	"startColumn": 52,
	"endLineNumber": 832,
	"endColumn": 62
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"challenges\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 844,
	"startColumn": 48,
	"endLineNumber": 844,
	"endColumn": 58
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"challenges\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 845,
	"startColumn": 54,
	"endLineNumber": 845,
	"endColumn": 64
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"data\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 851,
	"startColumn": 29,
	"endLineNumber": 851,
	"endColumn": 33
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"fun_facts\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 915,
	"startColumn": 29,
	"endLineNumber": 915,
	"endColumn": 38
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"fun_facts\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 921,
	"startColumn": 47,
	"endLineNumber": 921,
	"endColumn": 56
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"summary\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 973,
	"startColumn": 28,
	"endLineNumber": 973,
	"endColumn": 35
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"source_path\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 976,
	"startColumn": 25,
	"endLineNumber": 976,
	"endColumn": 36
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"source_path\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 977,
	"startColumn": 43,
	"endLineNumber": 977,
	"endColumn": 54
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"author\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 980,
	"startColumn": 39,
	"endLineNumber": 980,
	"endColumn": 45
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"version\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 981,
	"startColumn": 40,
	"endLineNumber": 981,
	"endColumn": 47
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"topic_type\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 982,
	"startColumn": 37,
	"endLineNumber": 982,
	"endColumn": 47
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/core/explorer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"name\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 1009,
	"startColumn": 75,
	"endLineNumber": 1009,
	"endColumn": 79
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/Hogwarts/great_hall/mistral_agent.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"agents.function_definitions\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 32,
	"startColumn": 10,
	"endLineNumber": 32,
	"endColumn": 37
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/Hogwarts/great_hall/mistral_agent.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \".agents.function_definitions\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 39,
	"startColumn": 10,
	"endLineNumber": 39,
	"endColumn": 38
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/Hogwarts/great_hall/mistral_agent.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"list[dict[str, str]]\" cannot be assigned to parameter \"messages\" of type \"List[Messages] | List[MessagesTypedDict]\" in function \"complete\"\n  Type \"list[dict[str, str]]\" is not assignable to type \"List[Messages] | List[MessagesTypedDict]\"\n    \"list[dict[str, str]]\" is not assignable to \"List[Messages]\"\n      Type parameter \"_T@list\" is invariant, but \"dict[str, str]\" is not the same as \"Messages\"\n      Consider switching from \"list\" to \"Sequence\" which is covariant\n    \"list[dict[str, str]]\" is not assignable to \"List[MessagesTypedDict]\"\n      Type parameter \"_T@list\" is invariant, but \"dict[str, str]\" is not the same as \"MessagesTypedDict\"\n      Consider switching from \"list\" to \"Sequence\" which is covariant",
	"source": "basedpyright",
	"startLineNumber": 138,
	"startColumn": 22,
	"endLineNumber": 138,
	"endColumn": 30
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/Hogwarts/great_hall/mistral_agent.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"continue_conversation\" for class \"Conversations\"\n  Attribute \"continue_conversation\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 162,
	"startColumn": 51,
	"endLineNumber": 162,
	"endColumn": 72
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/Hogwarts/great_hall/run_recommended_stream.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportReturnType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportReturnType"
		}
	},
	"severity": 8,
	"message": "Type \"tuple[Path, Path, Path, Path, Path]\" is not assignable to return type \"tuple[Path, Path, Path, Path]\"\n  \"tuple[Path, Path, Path, Path, Path]\" is not assignable to \"tuple[Path, Path, Path, Path]\"\n    Tuple size mismatch; expected 4 but received 5",
	"source": "basedpyright",
	"startLineNumber": 47,
	"startColumn": 12,
	"endLineNumber": 47,
	"endColumn": 78
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/Hogwarts/great_hall/run_recommended_stream.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Expression with type \"tuple[Path, Path, Path, Path]\" cannot be assigned to target tuple\n  Type \"tuple[Path, Path, Path, Path]\" is incompatible with target tuple\n    Tuple size mismatch; expected 5 but received 4",
	"source": "basedpyright",
	"startLineNumber": 117,
	"startColumn": 5,
	"endLineNumber": 117,
	"endColumn": 50
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/Hogwarts/great_hall/table/great_hall_table.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"Any | None\" cannot be assigned to parameter \"speaker_id\" of type \"str\" in function \"_resolve_speaker\"\n  Type \"Any | None\" is not assignable to type \"str\"\n    \"None\" is not assignable to \"str\"",
	"source": "basedpyright",
	"startLineNumber": 140,
	"startColumn": 88,
	"endLineNumber": 140,
	"endColumn": 105
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/Hogwarts/grid_bridge.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportReturnType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportReturnType"
		}
	},
	"severity": 8,
	"message": "Type \"dict[str, Any] | None\" is not assignable to return type \"dict[str, Any]\"\n  Type \"dict[str, Any] | None\" is not assignable to type \"dict[str, Any]\"\n    \"None\" is not assignable to \"dict[str, Any]\"",
	"source": "basedpyright",
	"startLineNumber": 813,
	"startColumn": 16,
	"endLineNumber": 813,
	"endColumn": 31
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/Hogwarts/spellbook_api.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"google_auth_oauthlib.flow\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 44,
	"startColumn": 10,
	"endLineNumber": 44,
	"endColumn": 35
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/Hogwarts/spellbook_api.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"googleapiclient.discovery\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 45,
	"startColumn": 10,
	"endLineNumber": 45,
	"endColumn": 35
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/scripts/chord_generator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"Path\" is not assignable to declared type \"str | None\"\n  Type \"Path\" is not assignable to type \"str | None\"\n    \"Path\" is not assignable to \"str\"\n    \"Path\" is not assignable to \"None\"",
	"source": "basedpyright",
	"startLineNumber": 70,
	"startColumn": 25,
	"endLineNumber": 70,
	"endColumn": 72
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/scripts/chord_generator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportCallIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportCallIssue"
		}
	},
	"severity": 8,
	"message": "No overloads for \"open\" match the provided arguments",
	"source": "basedpyright",
	"startLineNumber": 73,
	"startColumn": 18,
	"endLineNumber": 73,
	"endColumn": 56,
	"relatedInformation": [
		{
			"startLineNumber": 5621,
			"startColumn": 5,
			"endLineNumber": 5621,
			"endColumn": 9,
			"message": "Overload 7 is the closest match",
			"resource": "/c:/Users/irfan/.cursor/extensions/anysphere.cursorpyright-1.0.10/dist/typeshed-fallback/stdlib/builtins.pyi"
		}
	]
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/scripts/chord_generator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"str | None\" cannot be assigned to parameter \"file\" of type \"FileDescriptorOrPath\" in function \"open\"\n  Type \"str | None\" is not assignable to type \"FileDescriptorOrPath\"\n    Type \"None\" is not assignable to type \"FileDescriptorOrPath\"\n      \"None\" is not assignable to \"int\"\n      \"None\" is not assignable to \"str\"\n      \"None\" is not assignable to \"bytes\"\n      \"None\" is incompatible with protocol \"PathLike[str]\"\n        \"__fspath__\" is not present\n      \"None\" is incompatible with protocol \"PathLike[bytes]\"\n  ...",
	"source": "basedpyright",
	"startLineNumber": 73,
	"startColumn": 23,
	"endLineNumber": 73,
	"endColumn": 32
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/scripts/openai_smoketest.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"object\" is not assignable to declared type \"dict[Unknown, Unknown] | None\"\n  Type \"object\" is not assignable to type \"dict[Unknown, Unknown] | None\"\n    \"object\" is not assignable to \"dict[Unknown, Unknown]\"\n    \"object\" is not assignable to \"None\"",
	"source": "basedpyright",
	"startLineNumber": 87,
	"startColumn": 29,
	"endLineNumber": 87,
	"endColumn": 33
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/scripts/similarity_pie.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Expression with type \"tuple[list[Wedge], list[Text]] | tuple[list[Wedge], list[Text], list[Text]]\" cannot be assigned to target tuple\n  Type \"tuple[list[Wedge], list[Text]]\" is incompatible with target tuple\n    Tuple size mismatch; expected 3 but received 2",
	"source": "basedpyright",
	"startLineNumber": 126,
	"startColumn": 5,
	"endLineNumber": 126,
	"endColumn": 29
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/tests/test_story_eq.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"story_eq.config\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 16,
	"startColumn": 10,
	"endLineNumber": 16,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/tests/test_story_eq.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"story_eq.errors\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 17,
	"startColumn": 10,
	"endLineNumber": 17,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/tests/test_story_eq.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"story_eq.models\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 18,
	"startColumn": 10,
	"endLineNumber": 18,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/tests/test_story_eq.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"story_eq.parser\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 19,
	"startColumn": 10,
	"endLineNumber": 19,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/tests/test_story_eq.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"story_eq.validation\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 20,
	"startColumn": 10,
	"endLineNumber": 20,
	"endColumn": 29
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/tests/test_story_eq.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"story_eq.ui\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 324,
	"startColumn": 14,
	"endLineNumber": 324,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/tests/test_story_eq.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"story_eq.ui\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 330,
	"startColumn": 14,
	"endLineNumber": 330,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/tests/test_story_eq.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"story_eq.ui\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 336,
	"startColumn": 14,
	"endLineNumber": 336,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/tool/semantic_grep.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"sentence_transformers\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 100,
	"startColumn": 14,
	"endLineNumber": 100,
	"endColumn": 35
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"manim\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 10,
	"startColumn": 6,
	"endLineNumber": 10,
	"endColumn": 11
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Scene\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 13,
	"startColumn": 22,
	"endLineNumber": 13,
	"endColumn": 27
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Circle\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 20,
	"startColumn": 18,
	"endLineNumber": 20,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"BLUE\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 20,
	"startColumn": 41,
	"endLineNumber": 20,
	"endColumn": 45
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Create\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 21,
	"startColumn": 19,
	"endLineNumber": 21,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"VGroup\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 25,
	"startColumn": 22,
	"endLineNumber": 25,
	"endColumn": 28
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 27,
	"startColumn": 30,
	"endLineNumber": 27,
	"endColumn": 32
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 27,
	"startColumn": 47,
	"endLineNumber": 27,
	"endColumn": 49
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Text\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 28,
	"startColumn": 21,
	"endLineNumber": 28,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Write\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 31,
	"startColumn": 19,
	"endLineNumber": 31,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 36,
	"startColumn": 36,
	"endLineNumber": 36,
	"endColumn": 38
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 36,
	"startColumn": 53,
	"endLineNumber": 36,
	"endColumn": 55
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 37,
	"startColumn": 53,
	"endLineNumber": 37,
	"endColumn": 55
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 37,
	"startColumn": 70,
	"endLineNumber": 37,
	"endColumn": 72
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Arrow\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 40,
	"startColumn": 21,
	"endLineNumber": 40,
	"endColumn": 26
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"YELLOW\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 43,
	"startColumn": 23,
	"endLineNumber": 43,
	"endColumn": 29
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Text\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 49,
	"startColumn": 32,
	"endLineNumber": 49,
	"endColumn": 36
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"UP\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 49,
	"startColumn": 83,
	"endLineNumber": 49,
	"endColumn": 85
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"GrowArrow\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 52,
	"startColumn": 17,
	"endLineNumber": 52,
	"endColumn": 26
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Write\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 53,
	"startColumn": 17,
	"endLineNumber": 53,
	"endColumn": 22
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"FadeOut\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 57,
	"startColumn": 17,
	"endLineNumber": 57,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"FadeOut\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 58,
	"startColumn": 17,
	"endLineNumber": 58,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Text\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 62,
	"startColumn": 21,
	"endLineNumber": 62,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"UP\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 63,
	"startColumn": 27,
	"endLineNumber": 63,
	"endColumn": 29
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Write\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 64,
	"startColumn": 19,
	"endLineNumber": 64,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"BulletedList\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 67,
	"startColumn": 27,
	"endLineNumber": 67,
	"endColumn": 39
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"DOWN\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 74,
	"startColumn": 44,
	"endLineNumber": 74,
	"endColumn": 48
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Write\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 75,
	"startColumn": 19,
	"endLineNumber": 75,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"FadeOut\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 80,
	"startColumn": 13,
	"endLineNumber": 80,
	"endColumn": 20
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"FadeOut\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 81,
	"startColumn": 13,
	"endLineNumber": 81,
	"endColumn": 20
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"FadeOut\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 82,
	"startColumn": 13,
	"endLineNumber": 82,
	"endColumn": 20
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"FadeOut\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 83,
	"startColumn": 13,
	"endLineNumber": 83,
	"endColumn": 20
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Text\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 88,
	"startColumn": 23,
	"endLineNumber": 88,
	"endColumn": 27
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"UP\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 89,
	"startColumn": 29,
	"endLineNumber": 89,
	"endColumn": 31
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Write\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 90,
	"startColumn": 19,
	"endLineNumber": 90,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"BulletedList\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 93,
	"startColumn": 29,
	"endLineNumber": 93,
	"endColumn": 41
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"DOWN\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 100,
	"startColumn": 48,
	"endLineNumber": 100,
	"endColumn": 52
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Write\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 101,
	"startColumn": 19,
	"endLineNumber": 101,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"FadeOut\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 106,
	"startColumn": 13,
	"endLineNumber": 106,
	"endColumn": 20
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"FadeOut\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 107,
	"startColumn": 13,
	"endLineNumber": 107,
	"endColumn": 20
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Circle\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 112,
	"startColumn": 18,
	"endLineNumber": 112,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"BLUE\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 112,
	"startColumn": 41,
	"endLineNumber": 112,
	"endColumn": 45
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Create\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 113,
	"startColumn": 19,
	"endLineNumber": 113,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"VGroup\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 115,
	"startColumn": 22,
	"endLineNumber": 115,
	"endColumn": 28
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 117,
	"startColumn": 30,
	"endLineNumber": 117,
	"endColumn": 32
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 117,
	"startColumn": 47,
	"endLineNumber": 117,
	"endColumn": 49
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Text\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 118,
	"startColumn": 21,
	"endLineNumber": 118,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Write\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 121,
	"startColumn": 19,
	"endLineNumber": 121,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"VGroup\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 126,
	"startColumn": 30,
	"endLineNumber": 126,
	"endColumn": 36
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 130,
	"startColumn": 34,
	"endLineNumber": 130,
	"endColumn": 36
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 130,
	"startColumn": 51,
	"endLineNumber": 130,
	"endColumn": 53
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Dot\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 131,
	"startColumn": 19,
	"endLineNumber": 131,
	"endColumn": 22
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"RED\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 131,
	"startColumn": 59,
	"endLineNumber": 131,
	"endColumn": 62
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Text\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 132,
	"startColumn": 21,
	"endLineNumber": 132,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"RED\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 132,
	"startColumn": 51,
	"endLineNumber": 132,
	"endColumn": 54
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"UP\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 132,
	"startColumn": 69,
	"endLineNumber": 132,
	"endColumn": 71
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"VGroup\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 133,
	"startColumn": 36,
	"endLineNumber": 133,
	"endColumn": 42
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"FadeIn\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 137,
	"startColumn": 17,
	"endLineNumber": 137,
	"endColumn": 23
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Write\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 138,
	"startColumn": 17,
	"endLineNumber": 138,
	"endColumn": 22
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 149,
	"startColumn": 50,
	"endLineNumber": 149,
	"endColumn": 52
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 149,
	"startColumn": 67,
	"endLineNumber": 149,
	"endColumn": 69
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 150,
	"startColumn": 46,
	"endLineNumber": 150,
	"endColumn": 48
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PI\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 150,
	"startColumn": 63,
	"endLineNumber": 150,
	"endColumn": 65
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Arrow\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 152,
	"startColumn": 25,
	"endLineNumber": 152,
	"endColumn": 30
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"GREEN\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 155,
	"startColumn": 27,
	"endLineNumber": 155,
	"endColumn": 32
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"GrowArrow\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 159,
	"startColumn": 27,
	"endLineNumber": 159,
	"endColumn": 36
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"FadeOut\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 161,
	"startColumn": 27,
	"endLineNumber": 161,
	"endColumn": 34
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Text\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 164,
	"startColumn": 25,
	"endLineNumber": 164,
	"endColumn": 29
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"DOWN\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 165,
	"startColumn": 31,
	"endLineNumber": 165,
	"endColumn": 35
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/animated/manim_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Write\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 166,
	"startColumn": 19,
	"endLineNumber": 166,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/drive-index-vad/tools/locus_of_control_demo.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"workspace.dials_and_knobs\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 18,
	"startColumn": 6,
	"endLineNumber": 18,
	"endColumn": 31
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/drive-index-vad/tools/locus_of_control_demo.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"core.models\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 19,
	"startColumn": 6,
	"endLineNumber": 19,
	"endColumn": 17
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/interactive/plotly_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"plotly.graph_objects\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 33,
	"startColumn": 12,
	"endLineNumber": 33,
	"endColumn": 32
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/interactive/plotly_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"plotly.graph_objects\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 50,
	"startColumn": 16,
	"endLineNumber": 50,
	"endColumn": 36
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/interactive/plotly_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingModuleSource",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingModuleSource"
		}
	},
	"severity": 4,
	"message": "Import \"networkx\" could not be resolved from source",
	"source": "basedpyright",
	"startLineNumber": 32,
	"startColumn": 12,
	"endLineNumber": 32,
	"endColumn": 20
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/interactive/plotly_circle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingModuleSource",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingModuleSource"
		}
	},
	"severity": 4,
	"message": "Import \"networkx\" could not be resolved from source",
	"source": "basedpyright",
	"startLineNumber": 39,
	"startColumn": 16,
	"endLineNumber": 39,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/static/smartdecisor.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"None\" is not assignable to declared type \"List[str]\"\n  \"None\" is not assignable to \"List[str]\"",
	"source": "basedpyright",
	"startLineNumber": 46,
	"startColumn": 30,
	"endLineNumber": 46,
	"endColumn": 34
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/static/smartdecisor.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"None\" is not assignable to declared type \"Dict[str, str]\"\n  \"None\" is not assignable to \"Dict[str, str]\"",
	"source": "basedpyright",
	"startLineNumber": 47,
	"startColumn": 38,
	"endLineNumber": 47,
	"endColumn": 42
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/static/smartdecisor.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"None\" is not assignable to declared type \"List[str]\"\n  \"None\" is not assignable to \"List[str]\"",
	"source": "basedpyright",
	"startLineNumber": 50,
	"startColumn": 31,
	"endLineNumber": 50,
	"endColumn": 35
},{
	"resource": "/e:/grid/light_of_the_seven/demos/dataset_lifecycle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"sqlalchemy\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 25,
	"startColumn": 6,
	"endLineNumber": 25,
	"endColumn": 16
},{
	"resource": "/e:/grid/light_of_the_seven/demos/dataset_lifecycle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"sqlalchemy.orm\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 26,
	"startColumn": 6,
	"endLineNumber": 26,
	"endColumn": 20
},{
	"resource": "/e:/grid/light_of_the_seven/demos/dataset_lifecycle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"vinci_code.core.config\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 27,
	"startColumn": 6,
	"endLineNumber": 27,
	"endColumn": 28
},{
	"resource": "/e:/grid/light_of_the_seven/demos/dataset_lifecycle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"vinci_code.database.models\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 28,
	"startColumn": 6,
	"endLineNumber": 28,
	"endColumn": 32
},{
	"resource": "/e:/grid/light_of_the_seven/demos/dataset_lifecycle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"vinci_code.database.models_gfashion\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 29,
	"startColumn": 6,
	"endLineNumber": 29,
	"endColumn": 41
},{
	"resource": "/e:/grid/light_of_the_seven/demos/dataset_lifecycle.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"vinci_code.database.session\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 30,
	"startColumn": 6,
	"endLineNumber": 30,
	"endColumn": 33
},{
	"resource": "/e:/grid/light_of_the_seven/examples/grid_workflow_demo.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.grid.core.engine\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 19,
	"startColumn": 6,
	"endLineNumber": 19,
	"endColumn": 31
},{
	"resource": "/e:/grid/light_of_the_seven/examples/grid_workflow_demo.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.grid.core.fear\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 20,
	"startColumn": 6,
	"endLineNumber": 20,
	"endColumn": 29
},{
	"resource": "/e:/grid/light_of_the_seven/examples/grid_workflow_demo.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.grid.core.temporal\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 21,
	"startColumn": 6,
	"endLineNumber": 21,
	"endColumn": 33
},{
	"resource": "/e:/grid/light_of_the_seven/examples/grid_workflow_demo.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.grid.pattern.engine\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 22,
	"startColumn": 6,
	"endLineNumber": 22,
	"endColumn": 34
},{
	"resource": "/e:/grid/light_of_the_seven/examples/quantum_optimization_demo.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"circuits.services.quantum_utils\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 17,
	"startColumn": 6,
	"endLineNumber": 17,
	"endColumn": 37
},{
	"resource": "/e:/grid/light_of_the_seven/examples/translator_assistant_demo.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"services.translator_assistant\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 11,
	"startColumn": 6,
	"endLineNumber": 11,
	"endColumn": 35
},{
	"resource": "/e:/grid/light_of_the_seven/examples/translator_demo.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"grid.services.translator_assistant.service\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 12,
	"startColumn": 6,
	"endLineNumber": 12,
	"endColumn": 48
},{
	"resource": "/e:/grid/light_of_the_seven/grid/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \".essence.core_state\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 19,
	"startColumn": 10,
	"endLineNumber": 19,
	"endColumn": 29
},{
	"resource": "/e:/grid/light_of_the_seven/grid/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \".patterns.recognition\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 24,
	"startColumn": 10,
	"endLineNumber": 24,
	"endColumn": 31
},{
	"resource": "/e:/grid/light_of_the_seven/grid/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \".awareness.context\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 29,
	"startColumn": 10,
	"endLineNumber": 29,
	"endColumn": 28
},{
	"resource": "/e:/grid/light_of_the_seven/grid/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \".evolution.version\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 34,
	"startColumn": 10,
	"endLineNumber": 34,
	"endColumn": 28
},{
	"resource": "/e:/grid/light_of_the_seven/grid/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \".interfaces.bridge\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 39,
	"startColumn": 10,
	"endLineNumber": 39,
	"endColumn": 28
},{
	"resource": "/e:/grid/light_of_the_seven/grid/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "Operation on \"__all__\" is not supported, so exported symbol list may be incorrect",
	"source": "basedpyright",
	"startLineNumber": 72,
	"startColumn": 1,
	"endLineNumber": 120,
	"endColumn": 2
},{
	"resource": "/e:/grid/light_of_the_seven/grid/organization/org_manager.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"dict[str, list[str] | bool | None]\" cannot be assigned to parameter \"settings\" of type \"OrganizationSettings\" in function \"__init__\"",
	"source": "basedpyright",
	"startLineNumber": 29,
	"startColumn": 22,
	"endLineNumber": 34,
	"endColumn": 14
},{
	"resource": "/e:/grid/light_of_the_seven/grid/organization/org_manager.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"dict[str, list[str] | bool | None]\" cannot be assigned to parameter \"settings\" of type \"OrganizationSettings\" in function \"__init__\"",
	"source": "basedpyright",
	"startLineNumber": 44,
	"startColumn": 22,
	"endLineNumber": 49,
	"endColumn": 14
},{
	"resource": "/e:/grid/light_of_the_seven/grid/organization/org_manager.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"dict[str, list[str] | str | bool]\" cannot be assigned to parameter \"settings\" of type \"OrganizationSettings\" in function \"__init__\"",
	"source": "basedpyright",
	"startLineNumber": 59,
	"startColumn": 22,
	"endLineNumber": 64,
	"endColumn": 14
},{
	"resource": "/e:/grid/light_of_the_seven/grid/quantum/locomotion.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Quantizer\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 38,
	"startColumn": 45,
	"endLineNumber": 38,
	"endColumn": 54
},{
	"resource": "/e:/grid/light_of_the_seven/grid/senses/sensory_processor.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportGeneralTypeIssues",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportGeneralTypeIssues"
		}
	},
	"severity": 8,
	"message": "Expected class but received \"(obj: object, /) -> TypeIs[(...) -> object]\"",
	"source": "basedpyright",
	"startLineNumber": 13,
	"startColumn": 45,
	"endLineNumber": 13,
	"endColumn": 53
},{
	"resource": "/e:/grid/light_of_the_seven/grid/senses/sensory_processor.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Any\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 13,
	"startColumn": 80,
	"endLineNumber": 13,
	"endColumn": 83
},{
	"resource": "/e:/grid/light_of_the_seven/grid/senses/sensory_processor.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Any\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 26,
	"startColumn": 62,
	"endLineNumber": 26,
	"endColumn": 65
},{
	"resource": "/e:/grid/light_of_the_seven/grid/senses/sensory_processor.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Any\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 41,
	"startColumn": 70,
	"endLineNumber": 41,
	"endColumn": 73
},{
	"resource": "/e:/grid/light_of_the_seven/grid/senses/sensory_processor.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Any\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 50,
	"startColumn": 69,
	"endLineNumber": 50,
	"endColumn": 72
},{
	"resource": "/e:/grid/light_of_the_seven/grid/senses/sensory_processor.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Any\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 59,
	"startColumn": 68,
	"endLineNumber": 59,
	"endColumn": 71
},{
	"resource": "/e:/grid/light_of_the_seven/grid/senses/sensory_processor.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Any\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 67,
	"startColumn": 69,
	"endLineNumber": 67,
	"endColumn": 72
},{
	"resource": "/e:/grid/light_of_the_seven/grid/senses/sensory_processor.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Any\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 77,
	"startColumn": 69,
	"endLineNumber": 77,
	"endColumn": 72
},{
	"resource": "/e:/grid/light_of_the_seven/grid/senses/sensory_processor.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Any\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 88,
	"startColumn": 69,
	"endLineNumber": 88,
	"endColumn": 72
},{
	"resource": "/e:/grid/light_of_the_seven/grid/senses/sensory_processor.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Any\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 98,
	"startColumn": 75,
	"endLineNumber": 98,
	"endColumn": 78
},{
	"resource": "/e:/grid/light_of_the_seven/grid/senses/sensory_processor.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Any\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 107,
	"startColumn": 72,
	"endLineNumber": 107,
	"endColumn": 75
},{
	"resource": "/e:/grid/light_of_the_seven/grid/senses/sensory_processor.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Any\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 116,
	"startColumn": 73,
	"endLineNumber": 116,
	"endColumn": 76
},{
	"resource": "/e:/grid/light_of_the_seven/grid/senses/sensory_processor.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Any\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 125,
	"startColumn": 73,
	"endLineNumber": 125,
	"endColumn": 76
},{
	"resource": "/e:/grid/light_of_the_seven/grid/senses/sensory_processor.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Any\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 134,
	"startColumn": 75,
	"endLineNumber": 134,
	"endColumn": 78
},{
	"resource": "/e:/grid/light_of_the_seven/grid/tracing/trace_manager.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"TraceStore\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 14,
	"startColumn": 41,
	"endLineNumber": 14,
	"endColumn": 51
},{
	"resource": "/e:/grid/light_of_the_seven/grid/tracing/trace_manager.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportCallIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportCallIssue"
		}
	},
	"severity": 8,
	"message": "No parameter named \"error_traceback\"",
	"source": "basedpyright",
	"startLineNumber": 166,
	"startColumn": 57,
	"endLineNumber": 166,
	"endColumn": 72
},{
	"resource": "/e:/grid/light_of_the_seven/infra/cloud/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"aiohttp\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 27,
	"startColumn": 12,
	"endLineNumber": 27,
	"endColumn": 19
},{
	"resource": "/e:/grid/light_of_the_seven/infra/cloud/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"request\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 476,
	"startColumn": 42,
	"endLineNumber": 476,
	"endColumn": 49
},{
	"resource": "/e:/grid/light_of_the_seven/infra/cloud/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"request\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 486,
	"startColumn": 36,
	"endLineNumber": 486,
	"endColumn": 43
},{
	"resource": "/e:/grid/light_of_the_seven/infra/cloud/gemini_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"google.generativeai\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 45,
	"startColumn": 12,
	"endLineNumber": 45,
	"endColumn": 31
},{
	"resource": "/e:/grid/light_of_the_seven/infra/cloud/gemini_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportGeneralTypeIssues",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportGeneralTypeIssues"
		}
	},
	"severity": 8,
	"message": "\"object*\" is not awaitable\n  \"object*\" is incompatible with protocol \"Awaitable[_T_co@Awaitable]\"\n    \"__await__\" is not present",
	"source": "basedpyright",
	"startLineNumber": 142,
	"startColumn": 30,
	"endLineNumber": 142,
	"endColumn": 57
},{
	"resource": "/e:/grid/light_of_the_seven/infra/cloud/gemini_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportInvalidTypeForm",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportInvalidTypeForm"
		}
	},
	"severity": 8,
	"message": "Variable not allowed in type expression",
	"source": "basedpyright",
	"startLineNumber": 216,
	"startColumn": 37,
	"endLineNumber": 216,
	"endColumn": 42
},{
	"resource": "/e:/grid/light_of_the_seven/infra/cloud/gemini_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"ConnectError\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 362,
	"startColumn": 22,
	"endLineNumber": 362,
	"endColumn": 34
},{
	"resource": "/e:/grid/light_of_the_seven/infra/cloud/gemini_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"TimeoutException\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 364,
	"startColumn": 22,
	"endLineNumber": 364,
	"endColumn": 38
},{
	"resource": "/e:/grid/light_of_the_seven/infra/cloud/gemini_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"ConnectError\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 426,
	"startColumn": 22,
	"endLineNumber": 426,
	"endColumn": 34
},{
	"resource": "/e:/grid/light_of_the_seven/infra/cloud/gemini_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"TimeoutException\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 428,
	"startColumn": 22,
	"endLineNumber": 428,
	"endColumn": 38
},{
	"resource": "/e:/grid/light_of_the_seven/infra/cloud/gemini_client.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"ConnectError\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 492,
	"startColumn": 22,
	"endLineNumber": 492,
	"endColumn": 34
},{
	"resource": "/e:/grid/light_of_the_seven/infra/cloud/test_gemini_integration.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOperatorIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOperatorIssue"
		}
	},
	"severity": 8,
	"message": "Operator \"in\" not supported for types \"Literal['[MOCK]']\" and \"str | None\"\n  Operator \"in\" not supported for types \"Literal['[MOCK]']\" and \"None\"",
	"source": "basedpyright",
	"startLineNumber": 315,
	"startColumn": 16,
	"endLineNumber": 315,
	"endColumn": 41
},{
	"resource": "/e:/grid/light_of_the_seven/infra/cloud/test_gemini_integration.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOperatorIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOperatorIssue"
		}
	},
	"severity": 8,
	"message": "Operator \"in\" not supported for types \"Literal['[MOCK]']\" and \"str | None\"\n  Operator \"in\" not supported for types \"Literal['[MOCK]']\" and \"None\"",
	"source": "basedpyright",
	"startLineNumber": 325,
	"startColumn": 16,
	"endLineNumber": 325,
	"endColumn": 41
},{
	"resource": "/e:/grid/light_of_the_seven/light_of_the_seven/src/light_of_the_seven/integration.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"ibm_watsonx_ai\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 28,
	"startColumn": 10,
	"endLineNumber": 28,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/light_of_the_seven/src/light_of_the_seven/integration.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"torch\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 50,
	"startColumn": 12,
	"endLineNumber": 50,
	"endColumn": 17
},{
	"resource": "/e:/grid/light_of_the_seven/light_of_the_seven/tests/test_geometry.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"light_of_the_seven.geometry\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 11,
	"startColumn": 6,
	"endLineNumber": 11,
	"endColumn": 33
},{
	"resource": "/e:/grid/light_of_the_seven/light_of_the_seven/tests/test_integration.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"light_of_the_seven.integration\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 15,
	"startColumn": 6,
	"endLineNumber": 15,
	"endColumn": 36
},{
	"resource": "/e:/grid/light_of_the_seven/python/type_validator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "\"CognitiveState\" is unknown import symbol",
	"source": "basedpyright",
	"startLineNumber": 92,
	"startColumn": 13,
	"endLineNumber": 92,
	"endColumn": 27
},{
	"resource": "/e:/grid/light_of_the_seven/python/type_validator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "\"UserCognitiveProfile\" is unknown import symbol",
	"source": "basedpyright",
	"startLineNumber": 93,
	"startColumn": 13,
	"endLineNumber": 93,
	"endColumn": 33
},{
	"resource": "/e:/grid/light_of_the_seven/python/type_validator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "\"DecisionContext\" is unknown import symbol",
	"source": "basedpyright",
	"startLineNumber": 94,
	"startColumn": 13,
	"endLineNumber": 94,
	"endColumn": 28
},{
	"resource": "/e:/grid/light_of_the_seven/scripts/tap_report.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"acoustics.tap_model\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 16,
	"startColumn": 6,
	"endLineNumber": 16,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/scripts/validate_platform_integration.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "\"exceptions\" is not a known attribute of module \"jsonschema\"",
	"source": "basedpyright",
	"startLineNumber": 41,
	"startColumn": 23,
	"endLineNumber": 41,
	"endColumn": 33
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/heat_cooling_manager.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"scripts.heat_cooling_manager\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 6,
	"endLineNumber": 1,
	"endColumn": 34
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/no_mattter.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"scripts.no_mattter\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 5,
	"startColumn": 6,
	"endLineNumber": 5,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/orchestrator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"core.products.accelerator\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 15,
	"startColumn": 6,
	"endLineNumber": 15,
	"endColumn": 31
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Expected function name after \"def\"",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 1,
	"endLineNumber": 1,
	"endColumn": 4
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportGeneralTypeIssues",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportGeneralTypeIssues"
		}
	},
	"severity": 8,
	"message": "Expression cannot be assignment target",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 5,
	"endLineNumber": 1,
	"endColumn": 15
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 21,
	"endLineNumber": 1,
	"endColumn": 28
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Tkinter\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 21,
	"endLineNumber": 1,
	"endColumn": 28
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Tkinter\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 31,
	"endLineNumber": 1,
	"endColumn": 38
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"a\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 42,
	"endLineNumber": 1,
	"endColumn": 43
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 44,
	"endLineNumber": 1,
	"endColumn": 52
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"standard\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 44,
	"endLineNumber": 1,
	"endColumn": 52
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 53,
	"endLineNumber": 1,
	"endColumn": 60
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"library\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 53,
	"endLineNumber": 1,
	"endColumn": 60
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Python\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 64,
	"endLineNumber": 1,
	"endColumn": 70
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 71,
	"endLineNumber": 1,
	"endColumn": 75
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"that\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 71,
	"endLineNumber": 1,
	"endColumn": 75
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 76,
	"endLineNumber": 1,
	"endColumn": 84
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"provides\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 76,
	"endLineNumber": 1,
	"endColumn": 84
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 85,
	"endLineNumber": 1,
	"endColumn": 86
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"a\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 85,
	"endLineNumber": 1,
	"endColumn": 86
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 87,
	"endLineNumber": 1,
	"endColumn": 93
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"simple\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 87,
	"endLineNumber": 1,
	"endColumn": 93
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 94,
	"endLineNumber": 1,
	"endColumn": 101
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"toolkit\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 94,
	"endLineNumber": 1,
	"endColumn": 101
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 102,
	"endLineNumber": 1,
	"endColumn": 105
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Expected \"in\"",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 115,
	"endLineNumber": 1,
	"endColumn": 124
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"buttons\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 2,
	"startColumn": 1,
	"endLineNumber": 2,
	"endColumn": 8
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"text\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 2,
	"startColumn": 10,
	"endLineNumber": 2,
	"endColumn": 14
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 2,
	"startColumn": 15,
	"endLineNumber": 2,
	"endColumn": 20
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Expected expression",
	"source": "basedpyright",
	"startLineNumber": 2,
	"startColumn": 22,
	"endLineNumber": 2,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 3,
	"startColumn": 4,
	"endLineNumber": 3,
	"endColumn": 8
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PyQt\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 3,
	"startColumn": 4,
	"endLineNumber": 3,
	"endColumn": 8
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"PyQt\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 3,
	"startColumn": 11,
	"endLineNumber": 3,
	"endColumn": 15
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"a\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 3,
	"startColumn": 19,
	"endLineNumber": 3,
	"endColumn": 20
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 3,
	"startColumn": 21,
	"endLineNumber": 3,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 3,
	"startColumn": 25,
	"endLineNumber": 3,
	"endColumn": 27
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"of\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 3,
	"startColumn": 25,
	"endLineNumber": 3,
	"endColumn": 27
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 3,
	"startColumn": 28,
	"endLineNumber": 3,
	"endColumn": 36
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"bindings\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 3,
	"startColumn": 28,
	"endLineNumber": 3,
	"endColumn": 36
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 3,
	"startColumn": 37,
	"endLineNumber": 3,
	"endColumn": 40
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Expected \"in\"",
	"source": "basedpyright",
	"startLineNumber": 3,
	"startColumn": 45,
	"endLineNumber": 3,
	"endColumn": 47
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"extensive\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 4,
	"startColumn": 1,
	"endLineNumber": 4,
	"endColumn": 10
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 4,
	"startColumn": 11,
	"endLineNumber": 4,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"customization\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 4,
	"startColumn": 11,
	"endLineNumber": 4,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 4,
	"startColumn": 25,
	"endLineNumber": 4,
	"endColumn": 32
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Expected attribute name after \".\"",
	"source": "basedpyright",
	"startLineNumber": 4,
	"startColumn": 32,
	"endLineNumber": 4,
	"endColumn": 33
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 5,
	"startColumn": 4,
	"endLineNumber": 5,
	"endColumn": 12
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"wxPython\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 5,
	"startColumn": 4,
	"endLineNumber": 5,
	"endColumn": 12
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"wxPython\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 5,
	"startColumn": 15,
	"endLineNumber": 5,
	"endColumn": 23
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"another\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 5,
	"startColumn": 27,
	"endLineNumber": 5,
	"endColumn": 34
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 5,
	"startColumn": 35,
	"endLineNumber": 5,
	"endColumn": 38
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 5,
	"startColumn": 39,
	"endLineNumber": 5,
	"endColumn": 41
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"of\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 5,
	"startColumn": 39,
	"endLineNumber": 5,
	"endColumn": 41
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 5,
	"startColumn": 42,
	"endLineNumber": 5,
	"endColumn": 50
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"bindings\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 5,
	"startColumn": 42,
	"endLineNumber": 5,
	"endColumn": 50
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 5,
	"startColumn": 51,
	"endLineNumber": 5,
	"endColumn": 54
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Expected \"in\"",
	"source": "basedpyright",
	"startLineNumber": 5,
	"startColumn": 59,
	"endLineNumber": 5,
	"endColumn": 64
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 4,
	"endLineNumber": 7,
	"endColumn": 8
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Kivy\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 4,
	"endLineNumber": 7,
	"endColumn": 8
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Kivy\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 11,
	"endLineNumber": 7,
	"endColumn": 15
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"an\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 19,
	"endLineNumber": 7,
	"endColumn": 21
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 22,
	"endLineNumber": 7,
	"endColumn": 26
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"source\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 27,
	"endLineNumber": 7,
	"endColumn": 33
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 34,
	"endLineNumber": 7,
	"endColumn": 40
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Python\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 34,
	"endLineNumber": 7,
	"endColumn": 40
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 41,
	"endLineNumber": 7,
	"endColumn": 48
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"library\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 41,
	"endLineNumber": 7,
	"endColumn": 48
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 49,
	"endLineNumber": 7,
	"endColumn": 52
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Expected \"in\"",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 62,
	"endLineNumber": 7,
	"endColumn": 68
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"supports\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 8,
	"startColumn": 1,
	"endLineNumber": 8,
	"endColumn": 9
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 8,
	"startColumn": 10,
	"endLineNumber": 8,
	"endColumn": 15
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"multi\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 8,
	"startColumn": 10,
	"endLineNumber": 8,
	"endColumn": 15
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"touch\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 8,
	"startColumn": 16,
	"endLineNumber": 8,
	"endColumn": 21
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 8,
	"startColumn": 22,
	"endLineNumber": 8,
	"endColumn": 34
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"interactions\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 8,
	"startColumn": 22,
	"endLineNumber": 8,
	"endColumn": 34
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"other\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 8,
	"startColumn": 39,
	"endLineNumber": 8,
	"endColumn": 44
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 8,
	"startColumn": 45,
	"endLineNumber": 8,
	"endColumn": 51
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"modern\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 8,
	"startColumn": 45,
	"endLineNumber": 8,
	"endColumn": 51
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 8,
	"startColumn": 52,
	"endLineNumber": 8,
	"endColumn": 60
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Expected attribute name after \".\"",
	"source": "basedpyright",
	"startLineNumber": 8,
	"startColumn": 60,
	"endLineNumber": 8,
	"endColumn": 61
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 9,
	"startColumn": 4,
	"endLineNumber": 9,
	"endColumn": 9
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Bokeh\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 9,
	"startColumn": 4,
	"endLineNumber": 9,
	"endColumn": 9
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"Bokeh\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 9,
	"startColumn": 12,
	"endLineNumber": 9,
	"endColumn": 17
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"a\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 9,
	"startColumn": 21,
	"endLineNumber": 9,
	"endColumn": 22
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 9,
	"startColumn": 23,
	"endLineNumber": 9,
	"endColumn": 30
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"library\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 9,
	"startColumn": 23,
	"endLineNumber": 9,
	"endColumn": 30
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 9,
	"startColumn": 31,
	"endLineNumber": 9,
	"endColumn": 34
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Expected \"in\"",
	"source": "basedpyright",
	"startLineNumber": 9,
	"startColumn": 44,
	"endLineNumber": 9,
	"endColumn": 55
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"integrated\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 10,
	"startColumn": 1,
	"endLineNumber": 10,
	"endColumn": 11
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 10,
	"startColumn": 12,
	"endLineNumber": 10,
	"endColumn": 16
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"into\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 10,
	"startColumn": 12,
	"endLineNumber": 10,
	"endColumn": 16
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 10,
	"startColumn": 17,
	"endLineNumber": 10,
	"endColumn": 20
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 8,
	"message": "\"UIs\" is not defined",
	"source": "basedpyright",
	"startLineNumber": 10,
	"startColumn": 17,
	"endLineNumber": 10,
	"endColumn": 20
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Statements must be separated by newlines or semicolons",
	"source": "basedpyright",
	"startLineNumber": 10,
	"startColumn": 21,
	"endLineNumber": 10,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Expected \"in\"",
	"source": "basedpyright",
	"startLineNumber": 10,
	"startColumn": 30,
	"endLineNumber": 10,
	"endColumn": 41
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "\"{\" was not closed",
	"source": "basedpyright",
	"startLineNumber": 24,
	"startColumn": 1,
	"endLineNumber": 24,
	"endColumn": 2
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "\"(\" was not closed",
	"source": "basedpyright",
	"startLineNumber": 24,
	"startColumn": 2,
	"endLineNumber": 24,
	"endColumn": 3
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Unexpected indentation",
	"source": "basedpyright",
	"startLineNumber": 43,
	"startColumn": 1,
	"endLineNumber": 43,
	"endColumn": 9
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "\"[\" was not closed",
	"source": "basedpyright",
	"startLineNumber": 43,
	"startColumn": 9,
	"endLineNumber": 43,
	"endColumn": 10
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Expected expression",
	"source": "basedpyright",
	"startLineNumber": 43,
	"startColumn": 11,
	"endLineNumber": 43,
	"endColumn": 12
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Unindent not expected",
	"source": "basedpyright",
	"startLineNumber": 46,
	"startColumn": 1,
	"endLineNumber": 46,
	"endColumn": 2
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "\"{\" was not closed",
	"source": "basedpyright",
	"startLineNumber": 46,
	"startColumn": 1,
	"endLineNumber": 46,
	"endColumn": 2
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "\"(\" was not closed",
	"source": "basedpyright",
	"startLineNumber": 46,
	"startColumn": 2,
	"endLineNumber": 46,
	"endColumn": 3
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Unexpected indentation",
	"source": "basedpyright",
	"startLineNumber": 63,
	"startColumn": 1,
	"endLineNumber": 63,
	"endColumn": 7
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Expected expression",
	"source": "basedpyright",
	"startLineNumber": 63,
	"startColumn": 7,
	"endLineNumber": 63,
	"endColumn": 8
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"severity": 8,
	"message": "Unindent not expected",
	"source": "basedpyright",
	"startLineNumber": 65,
	"startColumn": 1,
	"endLineNumber": 65,
	"endColumn": 6
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 21,
	"endLineNumber": 1,
	"endColumn": 43
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 44,
	"endLineNumber": 1,
	"endColumn": 52
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 53,
	"endLineNumber": 1,
	"endColumn": 70
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 71,
	"endLineNumber": 1,
	"endColumn": 75
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 76,
	"endLineNumber": 1,
	"endColumn": 84
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 85,
	"endLineNumber": 1,
	"endColumn": 86
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 87,
	"endLineNumber": 1,
	"endColumn": 93
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 94,
	"endLineNumber": 1,
	"endColumn": 101
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 2,
	"startColumn": 1,
	"endLineNumber": 2,
	"endColumn": 14
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 3,
	"startColumn": 1,
	"endLineNumber": 3,
	"endColumn": 3
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 3,
	"startColumn": 4,
	"endLineNumber": 3,
	"endColumn": 20
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 3,
	"startColumn": 21,
	"endLineNumber": 3,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 3,
	"startColumn": 25,
	"endLineNumber": 3,
	"endColumn": 27
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 3,
	"startColumn": 28,
	"endLineNumber": 3,
	"endColumn": 36
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 4,
	"startColumn": 1,
	"endLineNumber": 4,
	"endColumn": 10
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 4,
	"startColumn": 11,
	"endLineNumber": 4,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 5,
	"startColumn": 1,
	"endLineNumber": 5,
	"endColumn": 3
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 5,
	"startColumn": 4,
	"endLineNumber": 5,
	"endColumn": 34
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 5,
	"startColumn": 35,
	"endLineNumber": 5,
	"endColumn": 38
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 5,
	"startColumn": 39,
	"endLineNumber": 5,
	"endColumn": 41
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 5,
	"startColumn": 42,
	"endLineNumber": 5,
	"endColumn": 50
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 1,
	"endLineNumber": 7,
	"endColumn": 3
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 4,
	"endLineNumber": 7,
	"endColumn": 21
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 22,
	"endLineNumber": 7,
	"endColumn": 33
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 34,
	"endLineNumber": 7,
	"endColumn": 40
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 7,
	"startColumn": 41,
	"endLineNumber": 7,
	"endColumn": 48
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 8,
	"startColumn": 1,
	"endLineNumber": 8,
	"endColumn": 9
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 8,
	"startColumn": 10,
	"endLineNumber": 8,
	"endColumn": 21
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 8,
	"startColumn": 22,
	"endLineNumber": 8,
	"endColumn": 44
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 8,
	"startColumn": 45,
	"endLineNumber": 8,
	"endColumn": 51
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 9,
	"startColumn": 1,
	"endLineNumber": 9,
	"endColumn": 3
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 9,
	"startColumn": 4,
	"endLineNumber": 9,
	"endColumn": 22
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 9,
	"startColumn": 23,
	"endLineNumber": 9,
	"endColumn": 30
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 10,
	"startColumn": 1,
	"endLineNumber": 10,
	"endColumn": 11
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 10,
	"startColumn": 12,
	"endLineNumber": 10,
	"endColumn": 16
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 10,
	"startColumn": 17,
	"endLineNumber": 10,
	"endColumn": 20
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 24,
	"startColumn": 1,
	"endLineNumber": 24,
	"endColumn": 12
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/simple_calc.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnusedExpression",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnusedExpression"
		}
	},
	"severity": 4,
	"message": "Expression value is unused",
	"source": "basedpyright",
	"startLineNumber": 46,
	"startColumn": 1,
	"endLineNumber": 46,
	"endColumn": 11
},{
	"resource": "/e:/grid/light_of_the_seven/tests/test_git_intelligence.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"git_intelligence\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 11,
	"startColumn": 6,
	"endLineNumber": 11,
	"endColumn": 22
},{
	"resource": "/e:/grid/light_of_the_seven/tests/test_grid_benchmark.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportGeneralTypeIssues",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportGeneralTypeIssues"
		}
	},
	"severity": 8,
	"message": "Expected class but received \"(iterable: Iterable[object], /) -> bool\"",
	"source": "basedpyright",
	"startLineNumber": 25,
	"startColumn": 34,
	"endLineNumber": 25,
	"endColumn": 37
},{
	"resource": "/e:/grid/light_of_the_seven/tests/test_grid_benchmark.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportReturnType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportReturnType"
		}
	},
	"severity": 8,
	"message": "Type \"dict[str, int | floating[Any] | Any]\" is not assignable to return type \"Dict[str, float]\"\n  \"floating[Any]\" is not assignable to \"float\"\n  \"floating[Any]\" is not assignable to \"float\"\n  \"floating[Any]\" is not assignable to \"float\"\n  \"floating[Any]\" is not assignable to \"float\"\n  \"floating[Any]\" is not assignable to \"float\"",
	"source": "basedpyright",
	"startLineNumber": 39,
	"startColumn": 16,
	"endLineNumber": 48,
	"endColumn": 10
},{
	"resource": "/e:/grid/light_of_the_seven/tests/test_tap_model.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"acoustics.tap_model\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 1,
	"startColumn": 6,
	"endLineNumber": 1,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/tests/test_version_3_5.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"grid.version_3_5\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 17,
	"startColumn": 6,
	"endLineNumber": 17,
	"endColumn": 22
},{
	"resource": "/e:/grid/light_of_the_seven/tests/test_version_4_5.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"grid.version_4_5\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 17,
	"startColumn": 6,
	"endLineNumber": 17,
	"endColumn": 22
},{
	"resource": "/e:/grid/light_of_the_seven/tests/test_version_4_5.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"grid.version_3_5\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 351,
	"startColumn": 14,
	"endLineNumber": 351,
	"endColumn": 30
},{
	"resource": "/e:/grid/light_of_the_seven/tools/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"tools.pulse_monitor\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 34,
	"startColumn": 14,
	"endLineNumber": 34,
	"endColumn": 33
},{
	"resource": "/e:/grid/light_of_the_seven/tools/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"tools.ambient_sound\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 38,
	"startColumn": 14,
	"endLineNumber": 38,
	"endColumn": 33
},{
	"resource": "/e:/grid/light_of_the_seven/tools/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"tools.ambient_sound\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 42,
	"startColumn": 14,
	"endLineNumber": 42,
	"endColumn": 33
},{
	"resource": "/e:/grid/light_of_the_seven/tools/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"tools.zoology_mapper\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 46,
	"startColumn": 14,
	"endLineNumber": 46,
	"endColumn": 34
},{
	"resource": "/e:/grid/light_of_the_seven/tools/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"tools.zoology_mapper\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 50,
	"startColumn": 14,
	"endLineNumber": 50,
	"endColumn": 34
},{
	"resource": "/e:/grid/light_of_the_seven/tools/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"PulseMonitor\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 23,
	"startColumn": 5,
	"endLineNumber": 23,
	"endColumn": 19
},{
	"resource": "/e:/grid/light_of_the_seven/tools/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"AmbientSoundGenerator\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 24,
	"startColumn": 5,
	"endLineNumber": 24,
	"endColumn": 28
},{
	"resource": "/e:/grid/light_of_the_seven/tools/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"ZoologyMapper\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 25,
	"startColumn": 5,
	"endLineNumber": 25,
	"endColumn": 20
},{
	"resource": "/e:/grid/light_of_the_seven/tools/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"SoundMetrics\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 26,
	"startColumn": 5,
	"endLineNumber": 26,
	"endColumn": 19
},{
	"resource": "/e:/grid/light_of_the_seven/tools/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"SensoryConfiguration\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 27,
	"startColumn": 5,
	"endLineNumber": 27,
	"endColumn": 27
},{
	"resource": "/e:/grid/light_of_the_seven/tools/rag/embeddings.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "\"Embedding\" is not a known attribute of module \"openai\"",
	"source": "basedpyright",
	"startLineNumber": 139,
	"startColumn": 31,
	"endLineNumber": 139,
	"endColumn": 40
},{
	"resource": "/e:/grid/light_of_the_seven/tools/rag/embeddings.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"sentence_transformers\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 159,
	"startColumn": 18,
	"endLineNumber": 159,
	"endColumn": 39
},{
	"resource": "/e:/grid/light_of_the_seven/tools/rag/indexer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"set[str]\" is not assignable to declared type \"List[str] | None\"\n  Type \"set[str]\" is not assignable to type \"List[str] | None\"\n    \"set[str]\" is not assignable to \"List[str]\"\n    \"set[str]\" is not assignable to \"None\"",
	"source": "basedpyright",
	"startLineNumber": 131,
	"startColumn": 24,
	"endLineNumber": 148,
	"endColumn": 10
},{
	"resource": "/e:/grid/light_of_the_seven/tools/rag/indexer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"reset\" for class \"BaseVectorStore\"\n  Attribute \"reset\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 209,
	"startColumn": 22,
	"endLineNumber": 209,
	"endColumn": 27
},{
	"resource": "/e:/grid/light_of_the_seven/tools/rag/indexer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOperatorIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOperatorIssue"
		}
	},
	"severity": 8,
	"message": "Operator \"not in\" not supported for types \"str\" and \"List[str] | None\"\n  Operator \"not in\" not supported for types \"str\" and \"None\"",
	"source": "basedpyright",
	"startLineNumber": 222,
	"startColumn": 39,
	"endLineNumber": 222,
	"endColumn": 60
},{
	"resource": "/e:/grid/light_of_the_seven/tools/rag/llm.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "\"ChatCompletion\" is not a known attribute of module \"openai\"",
	"source": "basedpyright",
	"startLineNumber": 41,
	"startColumn": 31,
	"endLineNumber": 41,
	"endColumn": 45
},{
	"resource": "/e:/grid/light_of_the_seven/tools/rag/rag_engine.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"List[float] | ndarray[_AnyShape, dtype[Any]]\" cannot be assigned to parameter \"query_embedding\" of type \"List[float]\" in function \"query\"\n  Type \"List[float] | ndarray[_AnyShape, dtype[Any]]\" is not assignable to type \"List[float]\"\n    \"ndarray[_AnyShape, dtype[Any]]\" is not assignable to \"List[float]\"",
	"source": "basedpyright",
	"startLineNumber": 122,
	"startColumn": 59,
	"endLineNumber": 122,
	"endColumn": 74
},{
	"resource": "/e:/grid/light_of_the_seven/tools/rag/rag_engine.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"list[Unknown]\" cannot be assigned to parameter \"value\" of type \"str\" in function \"__setitem__\"\n  \"list[Unknown]\" is not assignable to \"str\"",
	"source": "basedpyright",
	"startLineNumber": 159,
	"startColumn": 13,
	"endLineNumber": 159,
	"endColumn": 30
},{
	"resource": "/e:/grid/light_of_the_seven/tools/rag/rag_engine.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"List[List[float] | ndarray[_AnyShape, dtype[Any]]]\" cannot be assigned to parameter \"embeddings\" of type \"List[List[float]]\" in function \"add\"\n  \"List[List[float] | ndarray[_AnyShape, dtype[Any]]]\" is not assignable to \"List[List[float]]\"\n    Type parameter \"_T@list\" is invariant, but \"List[float] | ndarray[_AnyShape, dtype[Any]]\" is not the same as \"List[float]\"\n    Consider switching from \"list\" to \"Sequence\" which is covariant",
	"source": "basedpyright",
	"startLineNumber": 180,
	"startColumn": 72,
	"endLineNumber": 180,
	"endColumn": 82
},{
	"resource": "/e:/grid/light_of_the_seven/tools/rag/retriever.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"grid.rag.contracts\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 12,
	"startColumn": 10,
	"endLineNumber": 12,
	"endColumn": 28
},{
	"resource": "/e:/grid/light_of_the_seven/tools/rag/retriever.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"search\" for class \"VectorStore\"\n  Attribute \"search\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 71,
	"startColumn": 34,
	"endLineNumber": 71,
	"endColumn": 40
},{
	"resource": "/e:/grid/light_of_the_seven/tools/rag/retriever.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"search\" for class \"VectorStore\"\n  Attribute \"search\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 108,
	"startColumn": 31,
	"endLineNumber": 108,
	"endColumn": 37
},{
	"resource": "/e:/grid/light_of_the_seven/tools/rag/vector_store/chromadb_store.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"List[List[float]]\" cannot be assigned to parameter \"embeddings\" of type \"OneOrMany[Embedding] | OneOrMany[PyEmbedding] | None\" in function \"add\"\n  Type \"List[List[float]]\" is not assignable to type \"OneOrMany[Embedding] | OneOrMany[PyEmbedding] | None\"\n    \"List[List[float]]\" is not assignable to \"ndarray[_AnyShape, dtype[int32 | float32]]\"\n    \"List[List[float]]\" is not assignable to \"List[Embedding]\"\n      Type parameter \"_T@list\" is invariant, but \"List[float]\" is not the same as \"Embedding\"\n      Consider switching from \"list\" to \"Sequence\" which is covariant\n    \"List[List[float]]\" is not assignable to \"Sequence[float]\"\n      Type parameter \"_T_co@Sequence\" is covariant, but \"List[float]\" is not a subtype of \"float\"\n        \"List[float]\" is not assignable to \"float\"\n  ...",
	"source": "basedpyright",
	"startLineNumber": 69,
	"startColumn": 70,
	"endLineNumber": 69,
	"endColumn": 80
},{
	"resource": "/e:/grid/light_of_the_seven/tools/rag/vector_store/chromadb_store.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"List[Dict[str, Any]]\" cannot be assigned to parameter \"metadatas\" of type \"OneOrMany[Metadata] | None\" in function \"add\"\n  Type \"List[Dict[str, Any]]\" is not assignable to type \"OneOrMany[Metadata] | None\"\n    \"List[Dict[str, Any]]\" is not assignable to \"Mapping[str, str | int | float | bool | SparseVector | None]\"\n    \"List[Dict[str, Any]]\" is not assignable to \"List[Metadata]\"\n      Type parameter \"_T@list\" is invariant, but \"Dict[str, Any]\" is not the same as \"Metadata\"\n      Consider switching from \"list\" to \"Sequence\" which is covariant\n    \"List[Dict[str, Any]]\" is not assignable to \"None\"",
	"source": "basedpyright",
	"startLineNumber": 69,
	"startColumn": 92,
	"endLineNumber": 69,
	"endColumn": 101
},{
	"resource": "/e:/grid/light_of_the_seven/tools/rag/vector_store/chromadb_store.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"List[str]\" cannot be assigned to parameter \"include\" of type \"Include\" in function \"query\"\n  \"List[str]\" is not assignable to \"List[Literal['documents', 'embeddings', 'metadatas', 'distances', 'uris', 'data']]\"\n    Type parameter \"_T@list\" is invariant, but \"str\" is not the same as \"Literal['documents', 'embeddings', 'metadatas', 'distances', 'uris', 'data']\"\n    Consider switching from \"list\" to \"Sequence\" which is covariant",
	"source": "basedpyright",
	"startLineNumber": 93,
	"startColumn": 91,
	"endLineNumber": 93,
	"endColumn": 98
},{
	"resource": "/e:/grid/python/type_validator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "\"CognitiveState\" is unknown import symbol",
	"source": "basedpyright",
	"startLineNumber": 92,
	"startColumn": 13,
	"endLineNumber": 92,
	"endColumn": 27
},{
	"resource": "/e:/grid/python/type_validator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "\"UserCognitiveProfile\" is unknown import symbol",
	"source": "basedpyright",
	"startLineNumber": 93,
	"startColumn": 13,
	"endLineNumber": 93,
	"endColumn": 33
},{
	"resource": "/e:/grid/python/type_validator.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "\"DecisionContext\" is unknown import symbol",
	"source": "basedpyright",
	"startLineNumber": 94,
	"startColumn": 13,
	"endLineNumber": 94,
	"endColumn": 28
},{
	"resource": "/e:/grid/scripts/tap_report.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"acoustics.tap_model\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 16,
	"startColumn": 6,
	"endLineNumber": 16,
	"endColumn": 25
},{
	"resource": "/e:/grid/scripts/validate_platform_integration.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "\"exceptions\" is not a known attribute of module \"jsonschema\"",
	"source": "basedpyright",
	"startLineNumber": 41,
	"startColumn": 23,
	"endLineNumber": 41,
	"endColumn": 33
},{
	"resource": "/e:/grid/src/grid/analysis/clustering.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Expression of type \"None\" cannot be assigned to parameter of type \"float\"\n  \"None\" is not assignable to \"float\"",
	"source": "basedpyright",
	"startLineNumber": 37,
	"startColumn": 63,
	"endLineNumber": 37,
	"endColumn": 67
},{
	"resource": "/e:/grid/src/grid/analysis/clustering.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"Literal[-1]\" cannot be assigned to parameter \"value\" of type \"float64\" in function \"count\"\n  \"Literal[-1]\" is not assignable to \"float64\"",
	"source": "basedpyright",
	"startLineNumber": 89,
	"startColumn": 38,
	"endLineNumber": 89,
	"endColumn": 40
},{
	"resource": "/e:/grid/test_retry_limit.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"process_message\" for class \"MessageBroker\"\n  Attribute \"process_message\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 17,
	"startColumn": 31,
	"endLineNumber": 17,
	"endColumn": 46
},{
	"resource": "/e:/grid/tests/api/test_e2e.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportCallIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportCallIssue"
		}
	},
	"severity": 8,
	"message": "No parameter named \"timeout\"",
	"source": "basedpyright",
	"startLineNumber": 227,
	"startColumn": 54,
	"endLineNumber": 227,
	"endColumn": 61
},{
	"resource": "/e:/grid/tests/api/test_e2e.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportCallIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportCallIssue"
		}
	},
	"severity": 8,
	"message": "No parameter named \"timeout\"",
	"source": "basedpyright",
	"startLineNumber": 265,
	"startColumn": 50,
	"endLineNumber": 265,
	"endColumn": 57
},{
	"resource": "/e:/grid/tests/api/test_schemas.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"Literal['code']\" cannot be assigned to parameter \"context_type\" of type \"ContextType\" in function \"__init__\"\n  \"Literal['code']\" is not assignable to \"ContextType\"",
	"source": "basedpyright",
	"startLineNumber": 67,
	"startColumn": 26,
	"endLineNumber": 67,
	"endColumn": 32
},{
	"resource": "/e:/grid/tests/api/test_schemas.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportCallIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportCallIssue"
		}
	},
	"severity": 8,
	"message": "Arguments missing for parameters \"context\", \"paths\", \"envelope\"",
	"source": "basedpyright",
	"startLineNumber": 144,
	"startColumn": 20,
	"endLineNumber": 150,
	"endColumn": 10
},{
	"resource": "/e:/grid/tests/api/test_schemas.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportCallIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportCallIssue"
		}
	},
	"severity": 8,
	"message": "Arguments missing for parameters \"context\", \"paths\", \"envelope\"",
	"source": "basedpyright",
	"startLineNumber": 158,
	"startColumn": 13,
	"endLineNumber": 163,
	"endColumn": 14
},{
	"resource": "/e:/grid/tests/api/test_schemas.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportCallIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportCallIssue"
		}
	},
	"severity": 8,
	"message": "Argument missing for parameter \"envelope\"",
	"source": "basedpyright",
	"startLineNumber": 254,
	"startColumn": 19,
	"endLineNumber": 260,
	"endColumn": 10
},{
	"resource": "/e:/grid/tests/api/test_websocket.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportCallIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportCallIssue"
		}
	},
	"severity": 8,
	"message": "No parameter named \"timeout\"",
	"source": "basedpyright",
	"startLineNumber": 54,
	"startColumn": 50,
	"endLineNumber": 54,
	"endColumn": 57
},{
	"resource": "/e:/grid/tests/api/test_websocket.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportCallIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportCallIssue"
		}
	},
	"severity": 8,
	"message": "No parameter named \"timeout\"",
	"source": "basedpyright",
	"startLineNumber": 77,
	"startColumn": 51,
	"endLineNumber": 77,
	"endColumn": 58
},{
	"resource": "/e:/grid/tests/api/test_websocket.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportCallIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportCallIssue"
		}
	},
	"severity": 8,
	"message": "No parameter named \"timeout\"",
	"source": "basedpyright",
	"startLineNumber": 137,
	"startColumn": 50,
	"endLineNumber": 137,
	"endColumn": 57
},{
	"resource": "/e:/grid/tests/api/test_websocket.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportCallIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportCallIssue"
		}
	},
	"severity": 8,
	"message": "No parameter named \"timeout\"",
	"source": "basedpyright",
	"startLineNumber": 165,
	"startColumn": 50,
	"endLineNumber": 165,
	"endColumn": 57
},{
	"resource": "/e:/grid/tests/test_git_intelligence.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"git_intelligence\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 11,
	"startColumn": 6,
	"endLineNumber": 11,
	"endColumn": 22
},{
	"resource": "/e:/grid/tests/test_tap_model.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"acoustics.tap_model\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 5,
	"startColumn": 6,
	"endLineNumber": 5,
	"endColumn": 25
},{
	"resource": "/e:/grid/tests/test_version_3_5.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"grid.version_3_5\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 21,
	"startColumn": 6,
	"endLineNumber": 21,
	"endColumn": 22
},{
	"resource": "/e:/grid/tests/test_version_4_5.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"grid.version_4_5\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 21,
	"startColumn": 6,
	"endLineNumber": 21,
	"endColumn": 22
},{
	"resource": "/e:/grid/tests/test_version_4_5.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"grid.version_3_5\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 355,
	"startColumn": 14,
	"endLineNumber": 355,
	"endColumn": 30
},{
	"resource": "/e:/grid/tests/unit/test_pattern_engine_dbscan.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"None\" cannot be assigned to parameter \"eps\" of type \"float\" in function \"perform_dbscan\"\n  \"None\" is not assignable to \"float\"",
	"source": "basedpyright",
	"startLineNumber": 85,
	"startColumn": 51,
	"endLineNumber": 85,
	"endColumn": 55
},{
	"resource": "/e:/grid/tools/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"tools.pulse_monitor\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 34,
	"startColumn": 14,
	"endLineNumber": 34,
	"endColumn": 33
},{
	"resource": "/e:/grid/tools/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"tools.ambient_sound\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 38,
	"startColumn": 14,
	"endLineNumber": 38,
	"endColumn": 33
},{
	"resource": "/e:/grid/tools/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"tools.ambient_sound\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 42,
	"startColumn": 14,
	"endLineNumber": 42,
	"endColumn": 33
},{
	"resource": "/e:/grid/tools/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"tools.zoology_mapper\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 46,
	"startColumn": 14,
	"endLineNumber": 46,
	"endColumn": 34
},{
	"resource": "/e:/grid/tools/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"tools.zoology_mapper\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 50,
	"startColumn": 14,
	"endLineNumber": 50,
	"endColumn": 34
},{
	"resource": "/e:/grid/tools/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"PulseMonitor\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 23,
	"startColumn": 5,
	"endLineNumber": 23,
	"endColumn": 19
},{
	"resource": "/e:/grid/tools/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"AmbientSoundGenerator\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 24,
	"startColumn": 5,
	"endLineNumber": 24,
	"endColumn": 28
},{
	"resource": "/e:/grid/tools/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"ZoologyMapper\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 25,
	"startColumn": 5,
	"endLineNumber": 25,
	"endColumn": 20
},{
	"resource": "/e:/grid/tools/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"SoundMetrics\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 26,
	"startColumn": 5,
	"endLineNumber": 26,
	"endColumn": 19
},{
	"resource": "/e:/grid/tools/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"SensoryConfiguration\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 27,
	"startColumn": 5,
	"endLineNumber": 27,
	"endColumn": 27
},{
	"resource": "/e:/grid/tools/rag/embeddings.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "\"Embedding\" is not a known attribute of module \"openai\"",
	"source": "basedpyright",
	"startLineNumber": 139,
	"startColumn": 31,
	"endLineNumber": 139,
	"endColumn": 40
},{
	"resource": "/e:/grid/tools/rag/embeddings.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"sentence_transformers\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 159,
	"startColumn": 18,
	"endLineNumber": 159,
	"endColumn": 39
},{
	"resource": "/e:/grid/tools/rag/embeddings/nomic_v2.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportReturnType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportReturnType"
		}
	},
	"severity": 8,
	"message": "Type \"Sequence[float] | Any\" is not assignable to return type \"List[float]\"\n  Type \"Sequence[float] | Any\" is not assignable to type \"List[float]\"\n    \"Sequence[float]\" is not assignable to \"List[float]\"",
	"source": "basedpyright",
	"startLineNumber": 98,
	"startColumn": 32,
	"endLineNumber": 98,
	"endColumn": 41
},{
	"resource": "/e:/grid/tools/rag/hybrid_retriever.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingImports"
		}
	},
	"severity": 8,
	"message": "Import \"rank_bm25\" could not be resolved",
	"source": "basedpyright",
	"startLineNumber": 12,
	"startColumn": 10,
	"endLineNumber": 12,
	"endColumn": 19
},{
	"resource": "/e:/grid/tools/rag/hybrid_retriever.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalCall",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalCall"
		}
	},
	"severity": 8,
	"message": "Object of type \"None\" cannot be called",
	"source": "basedpyright",
	"startLineNumber": 91,
	"startColumn": 34,
	"endLineNumber": 91,
	"endColumn": 54
},{
	"resource": "/e:/grid/tools/rag/hybrid_retriever.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOptionalMemberAccess",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOptionalMemberAccess"
		}
	},
	"severity": 8,
	"message": "\"get_scores\" is not a known attribute of \"None\"",
	"source": "basedpyright",
	"startLineNumber": 134,
	"startColumn": 34,
	"endLineNumber": 134,
	"endColumn": 44
},{
	"resource": "/e:/grid/tools/rag/indexer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"set[str]\" is not assignable to declared type \"List[str] | None\"\n  Type \"set[str]\" is not assignable to type \"List[str] | None\"\n    \"set[str]\" is not assignable to \"List[str]\"\n    \"set[str]\" is not assignable to \"None\"",
	"source": "basedpyright",
	"startLineNumber": 139,
	"startColumn": 24,
	"endLineNumber": 156,
	"endColumn": 10
},{
	"resource": "/e:/grid/tools/rag/indexer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"reset\" for class \"BaseVectorStore\"\n  Attribute \"reset\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 229,
	"startColumn": 22,
	"endLineNumber": 229,
	"endColumn": 27
},{
	"resource": "/e:/grid/tools/rag/indexer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOperatorIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOperatorIssue"
		}
	},
	"severity": 8,
	"message": "Operator \"not in\" not supported for types \"str\" and \"List[str] | None\"\n  Operator \"not in\" not supported for types \"str\" and \"None\"",
	"source": "basedpyright",
	"startLineNumber": 264,
	"startColumn": 43,
	"endLineNumber": 264,
	"endColumn": 64
},{
	"resource": "/e:/grid/tools/rag/indexer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"set[str]\" is not assignable to declared type \"List[str] | None\"\n  Type \"set[str]\" is not assignable to type \"List[str] | None\"\n    \"set[str]\" is not assignable to \"List[str]\"\n    \"set[str]\" is not assignable to \"None\"",
	"source": "basedpyright",
	"startLineNumber": 430,
	"startColumn": 24,
	"endLineNumber": 434,
	"endColumn": 10
},{
	"resource": "/e:/grid/tools/rag/indexer.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportOperatorIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportOperatorIssue"
		}
	},
	"severity": 8,
	"message": "Operator \"not in\" not supported for types \"str\" and \"List[str] | None\"\n  Operator \"not in\" not supported for types \"str\" and \"None\"",
	"source": "basedpyright",
	"startLineNumber": 453,
	"startColumn": 39,
	"endLineNumber": 453,
	"endColumn": 60
},{
	"resource": "/e:/grid/tools/rag/llm.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "\"ChatCompletion\" is not a known attribute of module \"openai\"",
	"source": "basedpyright",
	"startLineNumber": 41,
	"startColumn": 31,
	"endLineNumber": 41,
	"endColumn": 45
},{
	"resource": "/e:/grid/tools/rag/rag_engine.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"List[float] | ndarray[_AnyShape, dtype[Any]]\" cannot be assigned to parameter \"query_embedding\" of type \"List[float]\" in function \"query\"\n  Type \"List[float] | ndarray[_AnyShape, dtype[Any]]\" is not assignable to type \"List[float]\"\n    \"ndarray[_AnyShape, dtype[Any]]\" is not assignable to \"List[float]\"",
	"source": "basedpyright",
	"startLineNumber": 154,
	"startColumn": 63,
	"endLineNumber": 154,
	"endColumn": 78
},{
	"resource": "/e:/grid/tools/rag/rag_engine.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"List[List[float] | ndarray[_AnyShape, dtype[Any]]]\" cannot be assigned to parameter \"embeddings\" of type \"List[List[float]]\" in function \"add\"\n  \"List[List[float] | ndarray[_AnyShape, dtype[Any]]]\" is not assignable to \"List[List[float]]\"\n    Type parameter \"_T@list\" is invariant, but \"List[float] | ndarray[_AnyShape, dtype[Any]]\" is not the same as \"List[float]\"\n    Consider switching from \"list\" to \"Sequence\" which is covariant",
	"source": "basedpyright",
	"startLineNumber": 241,
	"startColumn": 72,
	"endLineNumber": 241,
	"endColumn": 82
},{
	"resource": "/e:/grid/tools/rag/retriever.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"List[float]\" is not assignable to declared type \"Dict[str, float] | None\"\n  Type \"List[float]\" is not assignable to type \"Dict[str, float] | None\"\n    \"List[float]\" is not assignable to \"Dict[str, float]\"\n    \"List[float]\" is not assignable to \"None\"",
	"source": "basedpyright",
	"startLineNumber": 56,
	"startColumn": 33,
	"endLineNumber": 56,
	"endColumn": 63
},{
	"resource": "/e:/grid/tools/rag/retriever.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"str\" is not assignable to declared type \"int\"\n  \"str\" is not assignable to \"int\"",
	"source": "basedpyright",
	"startLineNumber": 72,
	"startColumn": 25,
	"endLineNumber": 72,
	"endColumn": 29
},{
	"resource": "/e:/grid/tools/rag/retriever.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"isdigit\" for class \"int\"\n  Attribute \"isdigit\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 73,
	"startColumn": 30,
	"endLineNumber": 73,
	"endColumn": 37
},{
	"resource": "/e:/grid/tools/rag/retriever.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAssignmentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAssignmentType"
		}
	},
	"severity": 8,
	"message": "Type \"list[float]\" is not assignable to declared type \"Dict[str, float] | None\"\n  Type \"list[float]\" is not assignable to type \"Dict[str, float] | None\"\n    \"list[float]\" is not assignable to \"Dict[str, float]\"\n    \"list[float]\" is not assignable to \"None\"",
	"source": "basedpyright",
	"startLineNumber": 75,
	"startColumn": 33,
	"endLineNumber": 75,
	"endColumn": 38
},{
	"resource": "/e:/grid/tools/rag/retriever.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportCallIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportCallIssue"
		}
	},
	"severity": 8,
	"message": "No parameter named \"n_results\"",
	"source": "basedpyright",
	"startLineNumber": 77,
	"startColumn": 50,
	"endLineNumber": 77,
	"endColumn": 59
},{
	"resource": "/e:/grid/tools/rag/retriever.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"Dict[str, float] | None\" cannot be assigned to parameter \"query_embedding\" of type \"Dict[str, float]\" in function \"query\"\n  Type \"Dict[str, float] | None\" is not assignable to type \"Dict[str, float]\"\n    \"None\" is not assignable to \"Dict[str, float]\"",
	"source": "basedpyright",
	"startLineNumber": 90,
	"startColumn": 37,
	"endLineNumber": 90,
	"endColumn": 46
},{
	"resource": "/e:/grid/tools/rag/retriever.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"search\" for class \"VectorStore\"\n  Attribute \"search\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 107,
	"startColumn": 34,
	"endLineNumber": 107,
	"endColumn": 40
},{
	"resource": "/e:/grid/tools/rag/retriever.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportAttributeAccessIssue"
		}
	},
	"severity": 8,
	"message": "Cannot access attribute \"search\" for class \"VectorStore\"\n  Attribute \"search\" is unknown",
	"source": "basedpyright",
	"startLineNumber": 144,
	"startColumn": 31,
	"endLineNumber": 144,
	"endColumn": 37
},{
	"resource": "/e:/grid/tools/rag/vector_store/chromadb_store.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"List[List[float]]\" cannot be assigned to parameter \"embeddings\" of type \"OneOrMany[Embedding] | OneOrMany[PyEmbedding] | None\" in function \"add\"\n  Type \"List[List[float]]\" is not assignable to type \"OneOrMany[Embedding] | OneOrMany[PyEmbedding] | None\"\n    \"List[List[float]]\" is not assignable to \"ndarray[_AnyShape, dtype[int32 | float32]]\"\n    \"List[List[float]]\" is not assignable to \"List[Embedding]\"\n      Type parameter \"_T@list\" is invariant, but \"List[float]\" is not the same as \"Embedding\"\n      Consider switching from \"list\" to \"Sequence\" which is covariant\n    \"List[List[float]]\" is not assignable to \"Sequence[float]\"\n      Type parameter \"_T_co@Sequence\" is covariant, but \"List[float]\" is not a subtype of \"float\"\n        \"List[float]\" is not assignable to \"float\"\n  ...",
	"source": "basedpyright",
	"startLineNumber": 69,
	"startColumn": 70,
	"endLineNumber": 69,
	"endColumn": 80
},{
	"resource": "/e:/grid/tools/rag/vector_store/chromadb_store.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"List[Dict[str, Any]]\" cannot be assigned to parameter \"metadatas\" of type \"OneOrMany[Metadata] | None\" in function \"add\"\n  Type \"List[Dict[str, Any]]\" is not assignable to type \"OneOrMany[Metadata] | None\"\n    \"List[Dict[str, Any]]\" is not assignable to \"Mapping[str, str | int | float | bool | SparseVector | None]\"\n    \"List[Dict[str, Any]]\" is not assignable to \"List[Metadata]\"\n      Type parameter \"_T@list\" is invariant, but \"Dict[str, Any]\" is not the same as \"Metadata\"\n      Consider switching from \"list\" to \"Sequence\" which is covariant\n    \"List[Dict[str, Any]]\" is not assignable to \"None\"",
	"source": "basedpyright",
	"startLineNumber": 69,
	"startColumn": 92,
	"endLineNumber": 69,
	"endColumn": 101
},{
	"resource": "/e:/grid/tools/rag/vector_store/chromadb_store.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportArgumentType",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportArgumentType"
		}
	},
	"severity": 8,
	"message": "Argument of type \"List[str]\" cannot be assigned to parameter \"include\" of type \"Include\" in function \"query\"\n  \"List[str]\" is not assignable to \"List[Literal['documents', 'embeddings', 'metadatas', 'distances', 'uris', 'data']]\"\n    Type parameter \"_T@list\" is invariant, but \"str\" is not the same as \"Literal['documents', 'embeddings', 'metadatas', 'distances', 'uris', 'data']\"\n    Consider switching from \"list\" to \"Sequence\" which is covariant",
	"source": "basedpyright",
	"startLineNumber": 93,
	"startColumn": 91,
	"endLineNumber": 93,
	"endColumn": 98
},{
	"resource": "/e:/grid/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"create_app\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 44,
	"startColumn": 5,
	"endLineNumber": 44,
	"endColumn": 17
},{
	"resource": "/e:/grid/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"app\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 45,
	"startColumn": 5,
	"endLineNumber": 45,
	"endColumn": 10
},{
	"resource": "/e:/grid/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"MothershipSettings\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 47,
	"startColumn": 5,
	"endLineNumber": 47,
	"endColumn": 25
},{
	"resource": "/e:/grid/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"get_settings\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 48,
	"startColumn": 5,
	"endLineNumber": 48,
	"endColumn": 19
},{
	"resource": "/e:/grid/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"CockpitService\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 50,
	"startColumn": 5,
	"endLineNumber": 50,
	"endColumn": 21
},{
	"resource": "/e:/grid/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"SessionService\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 51,
	"startColumn": 5,
	"endLineNumber": 51,
	"endColumn": 21
},{
	"resource": "/e:/grid/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"OperationService\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 52,
	"startColumn": 5,
	"endLineNumber": 52,
	"endColumn": 23
},{
	"resource": "/e:/grid/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"ComponentService\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 53,
	"startColumn": 5,
	"endLineNumber": 53,
	"endColumn": 23
},{
	"resource": "/e:/grid/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"AlertService\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 54,
	"startColumn": 5,
	"endLineNumber": 54,
	"endColumn": 19
},{
	"resource": "/e:/grid/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"Session\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 56,
	"startColumn": 5,
	"endLineNumber": 56,
	"endColumn": 14
},{
	"resource": "/e:/grid/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"Operation\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 57,
	"startColumn": 5,
	"endLineNumber": 57,
	"endColumn": 16
},{
	"resource": "/e:/grid/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"Component\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 58,
	"startColumn": 5,
	"endLineNumber": 58,
	"endColumn": 16
},{
	"resource": "/e:/grid/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"Alert\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 59,
	"startColumn": 5,
	"endLineNumber": 59,
	"endColumn": 12
},{
	"resource": "/e:/grid/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"CockpitState\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 60,
	"startColumn": 5,
	"endLineNumber": 60,
	"endColumn": 19
},{
	"resource": "/e:/grid/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"UnitOfWork\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 62,
	"startColumn": 5,
	"endLineNumber": 62,
	"endColumn": 17
},{
	"resource": "/e:/grid/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"StateStore\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 63,
	"startColumn": 5,
	"endLineNumber": 63,
	"endColumn": 17
},{
	"resource": "/e:/grid/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"MothershipError\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 65,
	"startColumn": 5,
	"endLineNumber": 65,
	"endColumn": 22
},{
	"resource": "/e:/grid/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"AuthenticationError\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 66,
	"startColumn": 5,
	"endLineNumber": 66,
	"endColumn": 26
},{
	"resource": "/e:/grid/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"AuthorizationError\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 67,
	"startColumn": 5,
	"endLineNumber": 67,
	"endColumn": 25
},{
	"resource": "/e:/grid/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"ResourceNotFoundError\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 68,
	"startColumn": 5,
	"endLineNumber": 68,
	"endColumn": 28
},{
	"resource": "/e:/grid/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"ValidationError\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 69,
	"startColumn": 5,
	"endLineNumber": 69,
	"endColumn": 22
},{
	"resource": "/e:/grid/datakit/visualizations/static/circle_graph.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingModuleSource",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingModuleSource"
		}
	},
	"severity": 4,
	"message": "Import \"networkx\" could not be resolved from source",
	"source": "basedpyright",
	"startLineNumber": 58,
	"startColumn": 16,
	"endLineNumber": 58,
	"endColumn": 24
},{
	"resource": "/e:/grid/datakit/visualizations/static/circle_graph.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingModuleSource",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingModuleSource"
		}
	},
	"severity": 4,
	"message": "Import \"networkx\" could not be resolved from source",
	"source": "basedpyright",
	"startLineNumber": 104,
	"startColumn": 16,
	"endLineNumber": 104,
	"endColumn": 24
},{
	"resource": "/e:/grid/grid/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "Operation on \"__all__\" is not supported, so exported symbol list may be incorrect",
	"source": "basedpyright",
	"startLineNumber": 101,
	"startColumn": 1,
	"endLineNumber": 122,
	"endColumn": 2
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"create_app\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 44,
	"startColumn": 5,
	"endLineNumber": 44,
	"endColumn": 17
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"app\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 45,
	"startColumn": 5,
	"endLineNumber": 45,
	"endColumn": 10
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"MothershipSettings\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 47,
	"startColumn": 5,
	"endLineNumber": 47,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"get_settings\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 48,
	"startColumn": 5,
	"endLineNumber": 48,
	"endColumn": 19
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"CockpitService\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 50,
	"startColumn": 5,
	"endLineNumber": 50,
	"endColumn": 21
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"SessionService\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 51,
	"startColumn": 5,
	"endLineNumber": 51,
	"endColumn": 21
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"OperationService\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 52,
	"startColumn": 5,
	"endLineNumber": 52,
	"endColumn": 23
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"ComponentService\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 53,
	"startColumn": 5,
	"endLineNumber": 53,
	"endColumn": 23
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"AlertService\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 54,
	"startColumn": 5,
	"endLineNumber": 54,
	"endColumn": 19
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"Session\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 56,
	"startColumn": 5,
	"endLineNumber": 56,
	"endColumn": 14
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"Operation\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 57,
	"startColumn": 5,
	"endLineNumber": 57,
	"endColumn": 16
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"Component\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 58,
	"startColumn": 5,
	"endLineNumber": 58,
	"endColumn": 16
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"Alert\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 59,
	"startColumn": 5,
	"endLineNumber": 59,
	"endColumn": 12
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"CockpitState\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 60,
	"startColumn": 5,
	"endLineNumber": 60,
	"endColumn": 19
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"UnitOfWork\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 62,
	"startColumn": 5,
	"endLineNumber": 62,
	"endColumn": 17
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"StateStore\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 63,
	"startColumn": 5,
	"endLineNumber": 63,
	"endColumn": 17
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"MothershipError\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 65,
	"startColumn": 5,
	"endLineNumber": 65,
	"endColumn": 22
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"AuthenticationError\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 66,
	"startColumn": 5,
	"endLineNumber": 66,
	"endColumn": 26
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"AuthorizationError\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 67,
	"startColumn": 5,
	"endLineNumber": 67,
	"endColumn": 25
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"ResourceNotFoundError\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 68,
	"startColumn": 5,
	"endLineNumber": 68,
	"endColumn": 28
},{
	"resource": "/e:/grid/light_of_the_seven/application/mothership/__init__.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportUnsupportedDunderAll",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportUnsupportedDunderAll"
		}
	},
	"severity": 4,
	"message": "\"ValidationError\" is specified in __all__ but is not present in module",
	"source": "basedpyright",
	"startLineNumber": 69,
	"startColumn": 5,
	"endLineNumber": 69,
	"endColumn": 22
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/static/circle_graph.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingModuleSource",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingModuleSource"
		}
	},
	"severity": 4,
	"message": "Import \"networkx\" could not be resolved from source",
	"source": "basedpyright",
	"startLineNumber": 58,
	"startColumn": 16,
	"endLineNumber": 58,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/datakit/visualizations/static/circle_graph.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingModuleSource",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingModuleSource"
		}
	},
	"severity": 4,
	"message": "Import \"networkx\" could not be resolved from source",
	"source": "basedpyright",
	"startLineNumber": 104,
	"startColumn": 16,
	"endLineNumber": 104,
	"endColumn": 24
},{
	"resource": "/e:/grid/light_of_the_seven/SEGA/generate_task_calendar.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingModuleSource",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingModuleSource"
		}
	},
	"severity": 4,
	"message": "Import \"icalendar\" could not be resolved from source",
	"source": "basedpyright",
	"startLineNumber": 8,
	"startColumn": 6,
	"endLineNumber": 8,
	"endColumn": 15
},{
	"resource": "/e:/grid/SEGA/generate_task_calendar.py",
	"owner": "basedpyright4",
	"code": {
		"value": "reportMissingModuleSource",
		"target": {
			"$mid": 1,
			"path": "/v1.32.1/configuration/config-files/",
			"scheme": "https",
			"authority": "docs.basedpyright.com",
			"fragment": "reportMissingModuleSource"
		}
	},
	"severity": 4,
	"message": "Import \"icalendar\" could not be resolved from source",
	"source": "basedpyright",
	"startLineNumber": 8,
	"startColumn": 6,
	"endLineNumber": 8,
	"endColumn": 15
}]

help me debug the errors im getting in my code

### Planner Response

I’ll tackle this by fixing the **real code/type bugs** first (things like wrong handler signatures, using `any` instead of `Any`, missing attributes on `StateStore`, mismatched model imports), and *separately* call out the **environment-only** issues (missing third‑party packages) that basedpyright reports but aren’t solvable purely in code.

First I’m going to open the specific files/line ranges that are producing the biggest errors so we can apply targeted patches.

*Updated todo list*

### Planner Response

I’m going to locate the exact offending code in `main.py` (exception handler registration), the middleware files, and where `StateStore` is defined/used. Once we see the concrete code, I’ll apply small, safe patches to satisfy basedpyright without changing behavior.

*Found code context*

*Viewed [main.py](file:///e:/grid/application/mothership/main.py) *

*Viewed [main.py](file:///e:/grid/application/mothership/main.py) *

*Viewed [__init__.py](file:///e:/grid/application/mothership/repositories/__init__.py) *

*Viewed [api_key.py](file:///e:/grid/application/mothership/repositories/api_key.py) *

*Viewed [payment.py](file:///e:/grid/application/mothership/repositories/payment.py) *

*Viewed [usage.py](file:///e:/grid/application/mothership/repositories/usage.py) *

### User Input



1. **Severity and impact** (e.g., blocking errors vs. warnings).
2. **Root causes** (e.g., missing dependencies, type mismatches, undefined variables).
3. **Project architecture** (respecting GRID's layered design and local-first principles).
4. **Cognitive layer integration** (ensuring fixes align with GRID's decision-support patterns).

---

## **Phase 1: Triage and Prioritization**
### **1.1 Categorize Issues by Type**
The diagnostics fall into the following broad categories:

| **Category**               | **Count** | **Priority** | **Description**                                                                                     |
|----------------------------|-----------|--------------|-----------------------------------------------------------------------------------------------------|
| Missing Imports            | ~100+     | **High**     | Modules/packages not found (e.g., `redis.asyncio`, `sqlalchemy`, `manim`, `openai`).               |
| Type Mismatches            | ~50+      | **High**     | Incorrect types passed to functions (e.g., `List[float]` vs. `Dict[str, float]`).                 |
| Attribute Access Errors    | ~40+      | **High**     | Accessing undefined attributes (e.g., `StateStore.api_keys`, `None.ping`).                         |
| Undefined Variables        | ~20+      | **High**     | Variables not defined (e.g., `Quantizer`, `TraceStore`).                                            |
| Optional Member Access     | ~30+      | **Medium**   | Accessing attributes on `None` (e.g., `None.ping`, `None.error_patterns`).                         |
| Invalid Type Forms         | ~10+      | **Medium**   | Incorrect type annotations (e.g., `Type annotation not supported for this statement`).             |
| Unsupported Dunder All     | ~10+      | **Low**      | `__all__` contains symbols not present in the module.                                              |
| Call Issues                | ~10+      | **High**     | Incorrect function calls (e.g., missing parameters, wrong argument types).                         |
| Return Type Mismatches     | ~5+       | **High**     | Functions return incorrect types (e.g., `Coroutine` vs. `Dict`).                                    |
| General Type Issues        | ~5+       | **Medium**   | Miscellaneous type errors (e.g., `Expected class but received "(...) -> bool"`).                   |

---

### **1.2 Prioritize by Impact**
#### **Critical (Fix Immediately)**
- **Missing Imports**: Block execution if dependencies are unresolved.
- **Type Mismatches**: Cause runtime errors if not fixed.
- **Attribute Access Errors**: Crash the application if accessed.
- **Undefined Variables**: Cause `NameError` at runtime.
- **Call Issues**: Break functionality if parameters are missing/wrong.

#### **High (Fix Next)**
- **Optional Member Access**: May cause `AttributeError` if `None` is not handled.
- **Return Type Mismatches**: Lead to incorrect behavior if not fixed.

#### **Medium/Low (Fix Later)**
- **Invalid Type Forms**: Affect type checking but may not break runtime.
- **Unsupported Dunder All**: Mostly a linting issue.

---

## **Phase 2: Root Cause Analysis**
### **2.1 Missing Imports**
#### **Common Causes**
1. **Uninstalled Dependencies**:
   - `redis.asyncio`, `sqlalchemy`, `manim`, `openai`, `sentence_transformers`, `google.generativeai`, `plotly`, `networkx`, `icalendar`.
   - **Solution**: Install missing packages via `pip` or `poetry`.
     ```bash
     pip install redis sqlalchemy manim openai sentence-transformers google-generativeai plotly networkx icalendar
     ```
   - **Note**: Some packages (e.g., `manim`, `networkx`) may require additional system dependencies.

2. **Incorrect Import Paths**:
   - `grid.api.routers`, `circuits.kernel.bus`, `light_of_the_seven.application.mothership.models`.
   - **Solution**: Verify module paths and refactor imports to match the project structure.

3. **Archival/Unused Code**:
   - Files in `archival/`, `SEGA/`, and `python_unclear/` may reference deprecated modules.
   - **Solution**: Either:
     - Remove unused code (if obsolete).
     - Restore missing modules (if still needed).

#### **Action Plan**
- **Step 1**: Run `pip install -r requirements.txt` (or equivalent) to ensure all dependencies are installed.
- **Step 2**: Use `grep` to find all missing imports and verify their locations:
  ```bash
  grep -r "Import.*could not be resolved" --include="*.py" .
  ```
- **Step 3**: For each missing import:
  - If the module exists but the path is wrong → Fix the import.
  - If the module is missing → Install it or remove the dependency.

---

### **2.2 Type Mismatches**
#### **Common Causes**
1. **Incorrect Type Annotations**:
   - Example: `List[float]` vs. `Dict[str, float]`.
   - **Solution**: Update type hints to match expected signatures.

2. **Coroutine vs. Sync Return Types**:
   - Example: `Coroutine[Any, Any, Dict]` returned where `Dict` is expected.
   - **Solution**: Use `await` or refactor to return the correct type.

3. **Literal vs. Enum Mismatches**:
   - Example: `Literal['warning']` vs. `AlertSeverity`.
   - **Solution**: Use the correct enum type (`AlertSeverity.WARNING`).

#### **Action Plan**
- **Step 1**: Focus on **high-impact** type mismatches first (e.g., `Coroutine` vs. `Dict`).
- **Step 2**: Use `basedpyright`'s suggestions to fix type hints.
- **Step 3**: For `Literal` vs. `Enum` issues, ensure enums are properly imported and used:
  ```python
  from enum import Enum

  class AlertSeverity(Enum):
      CRITICAL = "critical"
      WARNING = "warning"
      INFO = "info"
  ```

---

### **2.3 Attribute Access Errors**
#### **Common Causes**
1. **Undefined Attributes**:
   - Example: `StateStore.api_keys` does not exist.
   - **Solution**: Add the missing attribute to the class or use a valid attribute.

2. **Optional Member Access**:
   - Example: `None.ping` (accessing an attribute on `None`).
   - **Solution**: Add null checks (`if obj is not None`).

3. **Incorrect Class/Module Attributes**:
   - Example: `openai.Embedding` does not exist.
   - **Solution**: Verify the correct attribute name (e.g., `openai.Embedding.create`).

#### **Action Plan**
- **Step 1**: For `StateStore` errors, check if the class is properly defined:
  ```python
  class StateStore:
      api_keys: Dict[str, Any] = {}  # Add missing attribute
  ```
- **Step 2**: For `None` access errors, add null checks:
  ```python
  if redis_client is not None and hasattr(redis_client, "ping"):
      await redis_client.ping()
  ```
- **Step 3**: For incorrect module attributes (e.g., `openai.Embedding`), verify the correct API:
  ```python
  from openai import OpenAI
  client = OpenAI()
  embedding = client.embeddings.create(...)  # Correct usage
  ```

---

### **2.4 Undefined Variables**
#### **Common Causes**
1. **Missing Imports**:
   - Example: `Quantizer` not imported.
   - **Solution**: Import the missing class/function.

2. **Typographical Errors**:
   - Example: `Tkinter` vs. `tkinter`.
   - **Solution**: Fix typos.

3. **Uninitialized Variables**:
   - Example: `user_id` not defined.
   - **Solution**: Initialize the variable before use.

#### **Action Plan**
- **Step 1**: For each undefined variable, check if it should be imported or defined.
- **Step 2**: Fix typos (e.g., `Tkinter` → `tkinter`).
- **Step 3**: Initialize variables before use:
  ```python
  user_id = "default_user_id"  # Example initialization
  ```

---

### **2.5 Call Issues**
#### **Common Causes**
1. **Missing Parameters**:
   - Example: `No parameter named "proxies"`.
   - **Solution**: Remove or add the missing parameter.

2. **Incorrect Argument Types**:
   - Example: `List[float]` passed where `Dict[str, float]` is expected.
   - **Solution**: Convert the argument to the correct type.

#### **Action Plan**
- **Step 1**: For missing parameters, check the function signature and update calls.
- **Step 2**: For type mismatches, convert arguments:
  ```python
  # Convert List[float] to Dict[str, float]
  scores = {str(i): score for i, score in enumerate(scores_list)}
  ```

---

## **Phase 3: Implementation Strategy**
### **3.1 Fix Missing Imports**
1. **Install Dependencies**:
   ```bash
   pip install redis sqlalchemy manim openai sentence-transformers google-generativeai plotly networkx icalendar
   ```
2. **Verify Imports**:
   - Use `grep` to find all missing imports.
   - Fix paths or remove unused imports.

### **3.2 Fix Type Mismatches**
1. **Update Type Hints**:
   - Example: `List[float]` → `Dict[str, float]`.
2. **Handle Coroutines Properly**:
   - Example:
     ```python
     async def get_data() -> Dict[str, Any]:
         return {"key": "value"}
     ```
3. **Use Enums Instead of Literals**:
   - Example:
     ```python
     alert = Alert(severity=AlertSeverity.WARNING)  # Instead of "warning"
     ```

### **3.3 Fix Attribute Access Errors**
1. **Add Missing Attributes**:
   - Example:
     ```python
     class StateStore:
         api_keys: Dict[str, Any] = {}
     ```
2. **Add Null Checks**:
   - Example:
     ```python
     if redis_client is not None:
         await redis_client.ping()
     ```
3. **Verify Module Attributes**:
   - Example:
     ```python
     from openai import OpenAI
     client = OpenAI()
     embedding = client.embeddings.create(...)  # Correct usage
     ```

### **3.4 Fix Undefined Variables**
1. **Import Missing Classes**:
   - Example:
     ```python
     from some_module import Quantizer
     ```
2. **Fix Typos**:
   - Example: `Tkinter` → `tkinter`.
3. **Initialize Variables**:
   - Example:
     ```python
     user_id = "default_user_id"
     ```

### **3.5 Fix Call Issues**
1. **Remove/Update Parameters**:
   - Example:
     ```python
     # Remove "proxies" if not supported
     client = httpx.Client()
     ```
2. **Convert Argument Types**:
   - Example:
     ```python
     scores = {str(i): score for i, score in enumerate(scores_list)}
     ```

---

## **Phase 4: Validation and Testing**
### **4.1 Run Type Checking**
After fixes, run `basedpyright` to verify:
```bash
basedpyright .
```

### **4.2 Run Unit Tests**
Ensure existing tests pass:
```bash
pytest tests/
```

### **4.3 Manual Testing**
- Test critical paths (e.g., API endpoints, RAG system, payment flows).
- Verify that `None` checks and type conversions work as expected.

---

## **Phase 5: Long-Term Improvements**
### **5.1 Dependency Management**
- **Use `poetry` or `pip-tools`** to manage dependencies.
- **Document required packages** in `requirements.txt` or `pyproject.toml`.

### **5.2 Type Safety**
- **Enforce strict type checking** in `pyproject.toml`:
  ```toml
  [tool.basedpyright]
  typeCheckingMode = "strict"
  ```
- **Use `mypy` or `pyright`** alongside `basedpyright` for additional checks.

### **5.3 Code Reviews**
- **Add type hints** to all new code.
- **Review PRs for type safety** before merging.

### **5.4 Refactoring**
- **Remove dead code** (e.g., `archival/`, unused imports).
- **Standardize error handling** (e.g., custom exceptions for `None` access).

---

## **Phase 6: Example Fixes**
### **6.1 Fixing `StateStore` Attribute Errors**
**Problem**:
```python
# application/mothership/repositories/api_key.py
StateStore.api_keys = {}  # Error: Attribute "api_keys" is unknown
```
**Solution**:
```python
# application/mothership/models.py
class StateStore:
    api_keys: Dict[str, Any] = {}  # Add missing attribute
```

### **6.2 Fixing `None` Access Errors**
**Problem**:
```python
# application/mothership/middleware/rate_limit_redis.py
await redis_client.ping()  # Error: "ping" is not a known attribute of "None"
```
**Solution**:
```python
if redis_client is not None:
    await redis_client.ping()
```

### **6.3 Fixing Type Mismatches in Exception Handlers**
**Problem**:
```python
# application/mothership/main.py
@app.exception_handler(MothershipError)
async def handle_mothership_error(request: Request, exc: MothershipError) -> JSONResponse:
    return JSONResponse(...)  # Error: Type mismatch
```
**Solution**:
```python
from fastapi import HTTPException

@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(...)
```

### **6.4 Fixing Missing Imports**
**Problem**:
```python
# application/mothership/main.py
import grid.api.routers  # Error: Could not be resolved
```
**Solution**:
```python
# Verify the correct import path or remove if unused
from grid.api import routers  # Example fix
```

---

## **Phase 7: Tools to Automate Fixes**
### **7.1 Use `ruff` for Linting**
```bash
pip install ruff
ruff check .
```

### **7.2 Use `autoflake` to Remove Unused Imports**
```bash
pip install autoflake
autoflake --remove-all-unused-imports -i -r .
```

### **7.3 Use `isort` to Sort Imports**
```bash
pip install isort
isort .
```

---

## **Phase 8: Final Checklist**
| **Task**                          | **Status** |
|-----------------------------------|------------|
| Install missing dependencies       | ⬜         |
| Fix import paths                   | ⬜         |
| Resolve type mismatches            | ⬜         |
| Add missing attributes             | ⬜         |
| Add null checks                    | ⬜         |
| Fix undefined variables            | ⬜         |
| Update function calls              | ⬜         |
| Run `basedpyright`                 | ⬜         |
| Run unit tests                     | ⬜         |
| Manual testing                     | ⬜         |
| Document dependencies              | ⬜         |
| Enforce type checking in CI        | ⬜         |

---

## **Conclusion**
This plan systematically addresses the diagnostics by:
1. **Prioritizing high-impact issues** (missing imports, type mismatches, attribute errors).
2. **Fixing root causes** (dependencies, type hints, null checks).
3. **Validating changes** (type checking, tests, manual testing).
4. **Improving long-term maintainability** (dependency management, type safety, refactoring).

*Viewed [__init__.py](file:///e:/grid/application/mothership/repositories/__init__.py) *

*Edited relevant file*

### Planner Response

I’m going to fix the immediate syntax/formatting issue Ruff flagged in [main.py](file:///e:/grid/application/mothership/main.py:0:0-0:0) (a stray leading space on the new import), then address the next biggest type errors: the `any` vs `Any` annotation mistakes in the middleware, and the [StateStore](file:///e:/grid/application/mothership/repositories/__init__.py:112:0-186:9) / repository type mismatches (like the `ComponentHealth` coming from two different model modules).

*Grep searched codebase*

*Grep searched codebase*

*Grep searched codebase*

*Updated todo list*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Viewed [cockpit.py](file:///e:/grid/application/mothership/models/cockpit.py) *

*Viewed [__init__.py](file:///e:/grid/application/mothership/repositories/__init__.py) *

*Edited relevant file*

*Viewed [__init__.py](file:///e:/grid/application/mothership/models/__init__.py) *

*Edited relevant file*

### Planner Response

You’ve got a mix of **true code/type bugs** (fixable in-source) and **environment/dependency issues** (not fixable unless the packages/modules exist). I’ve already applied targeted fixes to the highest-impact *code* issues (FastAPI exception handler typing, `any` vs `Any`, optional Redis typing, and some cross-module enum mismatches). Next I’ll clean up the remaining “type mismatch due to duplicate model modules” pattern in [repositories/__init__.py](file:///e:/grid/application/mothership/repositories/__init__.py:0:0-0:0) by removing unused conflicting imports and a couple of unused runtime imports that are tripping Ruff/basedpyright.

*Edited relevant file*

### Planner Response

I’m going to (1) update the triage with what’s *actually* blocking vs. just type/lint noise, (2) summarize the concrete fixes I’ve already applied, and (3) point out the remaining error clusters and how to resolve them in a way that preserves GRID’s layered/local-first architecture. First, I’ll quickly re-open [repositories/__init__.py](file:///e:/grid/application/mothership/repositories/__init__.py:0:0-0:0) around the import section and the methods we touched to confirm the last patch applied cleanly.

*Viewed [__init__.py](file:///e:/grid/application/mothership/repositories/__init__.py) *

*Viewed [__init__.py](file:///e:/grid/application/mothership/repositories/__init__.py) *

*Viewed [__init__.py](file:///e:/grid/application/mothership/repositories/__init__.py) *

*Viewed [__init__.py](file:///e:/grid/application/mothership/repositories/__init__.py) *

*Updated todo list*

### Planner Response

I’m going to eliminate the remaining **real** basedpyright errors in the Mothership repositories ([api_key.py](file:///e:/grid/application/mothership/repositories/api_key.py:0:0-0:0), [payment.py](file:///e:/grid/application/mothership/repositories/payment.py:0:0-0:0), [usage.py](file:///e:/grid/application/mothership/repositories/usage.py:0:0-0:0)) by removing the “monkey-patch attributes onto [StateStore](file:///e:/grid/application/mothership/repositories/__init__.py:104:0-185:9) with inline type annotations” pattern. Since [StateStore](file:///e:/grid/application/mothership/repositories/__init__.py:104:0-185:9) now *declares* `api_keys`, `payment_transactions`, `subscriptions`, `invoices`, and `usage_records`, those blocks are unnecessary and are what triggered the “attribute unknown” + “type annotation not supported for this statement” errors. After that, I’ll summarize what’s left as **dependency/environment** vs **code** issues and how to address them without violating GRID’s layering/local-first principles.

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Updated todo list*

### Planner Response

## Triage (what’s *blocking* vs *noise*)

### **Blocking / high-impact (will break runtime or prevent import)**
- **Missing imports for optional/third-party modules**
  - Examples in your log: `redis.asyncio`, `rank_bm25`, `sentence_transformers`, `networkx`, `icalendar`, plus `grid.api.routers`/`tools.*` modules that don’t exist on disk or aren’t on `PYTHONPATH`.
  - These are *environment / packaging* problems or *wrong import paths*.
- **True API mismatches**
  - Example: `openai.Embedding` / `openai.ChatCompletion` errors: those symbols depend on **which OpenAI SDK you installed** (old vs new API). This needs code changes in your RAG layer.

### **Non-blocking / type-checker-only (but worth fixing)**
- FastAPI exception handler signature typing (basedpyright strictness).
- “Expected class but received `(iterable) -> bool`” (usually you wrote `Optional[any]` or `any` somewhere, where `Any` was intended).
- Repository `StateStore.*` attributes unknown due to runtime monkey-patching.

---

## Root causes (confirmed from your code)

### **1) FastAPI exception handlers (type mismatch)**
**Cause:** `FastAPI.add_exception_handler` expects a handler typed as `Callable[[Request, Exception], Response]` (simplified). Your handlers were narrower (`exc: MothershipError`, etc.), which is valid at runtime but fails strict typing.

**Fix applied (code-level):**
- In [application/mothership/main.py](file:///e:/grid/application/mothership/main.py:0:0-0:0), I widened handler params to `exc: Exception` and used `cast(...)` inside each handler.
- This keeps runtime behavior the same but satisfies basedpyright.

### **2) `any` vs `Any` (middleware “Expected class but received bool”)**
**Cause:** You used the built-in function `any` in type positions (ex: `Optional[any]`), so the type checker sees “a function”, not a type.

**Fix applied:**
- In [middleware/rate_limit_redis.py](file:///e:/grid/application/mothership/middleware/rate_limit_redis.py:0:0-0:0) and [middleware/usage_tracking.py](file:///e:/grid/application/mothership/middleware/usage_tracking.py:0:0-0:0), replaced `any` with `Any` and made `call_next` a properly typed callable.

### **3) Redis optional import + optional member access**
**Cause:**
- basedpyright flags `import redis.asyncio` as missing if redis isn’t installed.
- It also flags [.ping()](file:///e:/grid/application/mothership/main.py:418:4-421:31) on possibly-None redis client.

**Fix applied (local-first friendly):**
- Use `importlib.import_module("redis.asyncio")` inside [_ensure_redis()](file:///e:/grid/application/mothership/middleware/rate_limit_redis.py:62:4-87:42) so redis becomes a **soft dependency**.
- Narrowed `redis_client` before calling [.ping()](file:///e:/grid/application/mothership/main.py:418:4-421:31).
- This matches your architecture: Redis-backed limiter *only if available*, otherwise fallback memory limiter.

### **4) [StateStore](file:///e:/grid/application/mothership/repositories/__init__.py:104:0-185:9) attribute errors + invalid type forms**
**Cause:**
- Repositories were doing runtime monkey-patching like:
  - `self._store.api_keys: dict[str, APIKey] = {}`
- basedpyright dislikes this pattern (“type annotation not supported for this statement”) and also complains `api_keys` isn’t declared on [StateStore](file:///e:/grid/application/mothership/repositories/__init__.py:104:0-185:9).

**Fix applied (clean layering):**
- In [repositories/__init__.py](file:///e:/grid/application/mothership/repositories/__init__.py:0:0-0:0), I added these fields to the [StateStore](file:///e:/grid/application/mothership/repositories/__init__.py:104:0-185:9) dataclass:
  - `api_keys`, `payment_transactions`, `subscriptions`, `invoices`, `usage_records`
- Then removed the monkey-patching blocks from:
  - [repositories/api_key.py](file:///e:/grid/application/mothership/repositories/api_key.py:0:0-0:0)
  - [repositories/payment.py](file:///e:/grid/application/mothership/repositories/payment.py:0:0-0:0)
  - [repositories/usage.py](file:///e:/grid/application/mothership/repositories/usage.py:0:0-0:0)

This is the correct “source of truth” approach and fits GRID’s **layered design** (store defines state schema; repos operate on it).

### **5) Cross-module type mismatch ([ComponentHealth](file:///e:/grid/application/mothership/models/__init__.py:73:0-79:23) from two modules)**
**Cause:** You had *two different* [ComponentHealth](file:///e:/grid/application/mothership/models/__init__.py:73:0-79:23) enums:
- [application.mothership.models.ComponentHealth](file:///e:/grid/application/mothership/models/__init__.py:73:0-79:23)
- [application.mothership.models.cockpit.ComponentHealth](file:///e:/grid/application/mothership/models/__init__.py:73:0-79:23)

Even if values match, the type checker treats them as different types.

**Fix applied:**
- Adjusted repository annotations to refer to the cockpit model types (via `TYPE_CHECKING` aliases) where those are the ones actually stored in [StateStore](file:///e:/grid/application/mothership/repositories/__init__.py:104:0-185:9).

---

## What’s still failing (and why)

### **A) `grid.api.routers` missing**
In [main.py](file:///e:/grid/application/mothership/main.py:0:0-0:0) there is:
- a conditional `MOTHERSHIP_ENABLE_GRID_PULSE` import.

I already switched it to dynamic import:
- `importlib.import_module("grid.api.routers.pulse")`

If basedpyright still says `"Import grid.api.routers could not be resolved"`, it means:
- the module path **does not exist**, or
- the `grid/` package isn’t in the interpreter environment that basedpyright is using.

**Action choices (architecture-safe):**
- **If this is optional:** keep as dynamic import (already done) and ensure basedpyright is configured with the right `pythonPath` / venv.
- **If it must exist:** we need to locate where the actual routers live and fix the import path. (I can do this next with a targeted search for `pulse.router` and `grid/api/routers` folder.)

### **B) RAG layer failures (OpenAI / Chroma / rank_bm25 / sentence-transformers)**
These are a mix:
- **Missing third-party deps**: `rank_bm25`, `sentence_transformers`
- **OpenAI API mismatch**: `openai.ChatCompletion` and `openai.Embedding` depend on old SDK patterns.
- **Chroma typing**: includes/metadata/embedding typing mismatch (usually fine at runtime but strict typing complains).

**Recommended GRID-aligned strategy:**
- Treat embeddings/providers as **pluggable cognitive adapters**:
  - Local-first default: `sentence-transformers` (offline embeddings)
  - Optional cloud: OpenAI embeddings/chat (requires API key)
- Make these imports **soft** (like we did for Redis) so the app still runs without cloud deps.

If you want, I can patch the RAG modules to:
- use the modern OpenAI client pattern *or* gate it behind optional imports,
- standardize embedding return type to `list[float]` everywhere.

### **C) `tools.*` modules missing + `__all__` warnings
Those are mostly:
- files referenced in `tools/__init__.py` but not present,
- `__all__` listing items that aren’t actually importable.

This is *not runtime-breaking unless those imports are executed*, but basedpyright will complain.

---

## Cognitive layer integration (decision-support alignment)

What we did is consistent with “decision-support patterns”:
- **Hard dependencies** only for core runtime.
- **Optional capabilities** (Redis, Grid Pulse router, RAG providers) are now import-gated, enabling:
  - local-first execution,
  - graceful degradation,
  - clearer operational posture (capability detected at runtime).

This reduces “cognitive load” by making system capabilities explicit: *if installed → enabled; else → fallback*.

---

## Next step options (pick one)

### Option 1: **Focus on getting `mothership` clean**
- Fix remaining basedpyright errors inside `application/mothership/**`
- Ignore `tools/` and `tools/rag/**` for now

### Option 2: **Fix RAG subsystem properly**
- Standardize embeddings types (`list[float]`)
- Update OpenAI integration to match installed SDK (you tell me which package/version you use)
- Make `rank_bm25` and `sentence_transformers` optional with clean fallbacks

### Option 3: **Dependency audit**
- Identify which missing imports are:
  - required for your target deployment
  - archival/unused
- Then either install or gate/remove

Tell me which option you want, and (for Option 2) whether you’re using the **new** `openai` SDK (`from openai import OpenAI`) or an older one.

## Status
- **Completed:** fixes for [main.py](file:///e:/grid/application/mothership/main.py:0:0-0:0) exception handlers, redis middleware typing/imports, [StateStore](file:///e:/grid/application/mothership/repositories/__init__.py:104:0-185:9) attribute/type-form errors, and repository enum mismatch direction.
- **In progress:** summarizing & resolving remaining dependency/environment issues (pending your preference on scope).

*Viewed [main.py](file:///e:/grid/application/mothership/main.py) *

*Edited relevant file*

### User Input

create a master plan for simplifying and optimzing directory structure. there are several directories currently with same names causing import issues and confusion. navigate the project and come up with a smart and clever idea to resolve this without breaking any functionality. im aiming for a organizational cleanup and proper layout and arrangement of files and folders for a smooth and clean project navigation and functionality. identify any mismatches, import errors, module related errors, bad directory name structures and similar other gaps in the project and create a plan that will address these gaps and executing the plan should not break functionality, simultanelously the outcome should be a clean and organized project structure.

*Updated todo list*

### Planner Response

I’ll first map the current top-level package roots and identify where duplicate directory names (like multiple `mothership/`, `models/`, `tools/`) exist and how they’re being imported. Then I’ll propose a **target layout + a safe migration strategy** (compat shims + incremental moves) that avoids breaking runtime behavior while cleaning imports and aligning with GRID’s layered/local-first design. I won’t move or edit anything until you confirm the plan.

*Listed directory [grid](file:///e:/grid) *

*Searched filesystem*

*Searched filesystem*

*Searched filesystem*

*Searched filesystem*

*Searched filesystem*

*Searched filesystem*

### Planner Response

I’m going to inspect the repo’s [pyproject.toml](file:///e:/grid/pyproject.toml:0:0-0:0) (and a few key directories like [application/](file:///e:/grid/application:0:0-0:0), [mothership/](file:///e:/grid/mothership:0:0-0:0), [models/](file:///e:/grid/models:0:0-0:0), [src/](file:///e:/grid/src:0:0-0:0), [light_of_the_seven/](file:///e:/grid/light_of_the_seven:0:0-0:0)) to identify which folders are acting as *Python package roots* today and where same-named packages exist in multiple places. Then I’ll propose a **master re-org plan** that uses incremental moves + compatibility shims so functionality doesn’t break.

*Viewed [pyproject.toml](file:///e:/grid/pyproject.toml) *

*Listed directory [application](file:///e:/grid/application) *

*Listed directory [mothership](file:///e:/grid/mothership) *

*Listed directory [models](file:///e:/grid/models) *

*Listed directory [src](file:///e:/grid/src) *

*Listed directory [light_of_the_seven](file:///e:/grid/light_of_the_seven) *

*Searched filesystem*

*Searched filesystem*

*Searched filesystem*

*Searched filesystem*

*Searched filesystem*

*Grep searched codebase*

*Grep searched codebase*

*Grep searched codebase*

*Grep searched codebase*

*Grep searched codebase*

*Viewed [__init__.py](file:///e:/grid/application/mothership/__init__.py) *

*Viewed [__init__.py](file:///e:/grid/tools/__init__.py) *

*Viewed [__init__.py](file:///e:/grid/light_of_the_seven/tools/__init__.py) *

*Viewed [orchestrator.py](file:///e:/grid/SEGA/orchestrator.py) *

*Viewed [main.py](file:///e:/grid/src/cli/main.py) *

*Viewed [__init__.py](file:///e:/grid/grid/__init__.py) *

*Listed directory [grid](file:///e:/grid/grid) *

*Listed directory [grid](file:///e:/grid/src/grid) *

*Listed directory [mothership](file:///e:/grid/application/mothership) *

*Listed directory [tools](file:///e:/grid/tools) *

*Listed directory [services](file:///e:/grid/src/services) *

*Listed directory [models](file:///e:/grid/models) *

*Updated todo list*

*Listed directory [core](file:///e:/grid/core) *

*Listed directory [resonance](file:///e:/grid/application/resonance) *

*Listed directory [rag](file:///e:/grid/tools/rag) *

*Searched filesystem*

*Searched filesystem*

*Grep searched codebase*

*Grep searched codebase*

### Planner Response

I’ll now draft a **master re-organization plan** based on the concrete duplicates we found ([light_of_the_seven/](file:///e:/grid/light_of_the_seven:0:0-0:0) full mirror, [grid/](file:///e:/grid:0:0-0:0) vs [src/grid](file:///e:/grid/src/grid:0:0-0:0), root-level [models/](file:///e:/grid/models:0:0-0:0) and [tools/](file:///e:/grid/tools:0:0-0:0), and the Node [mothership/](file:///e:/grid/mothership:0:0-0:0) folder). Before I propose the final target layout, I’m going to quickly read your existing architecture/project-structure guidance (in `.cursor/rules/*`) plus the main [grid](file:///e:/grid:0:0-0:0) entry point so the plan matches your intended direction.

*Viewed [project_structure.md](file:///e:/grid/.cursor/rules/project_structure.md) *

*Viewed [architecture.md](file:///e:/grid/.cursor/rules/architecture.md) *

*Viewed [__main__.py](file:///e:/grid/grid/__main__.py) *

*Viewed [README.md](file:///e:/grid/README.md) *

*Grep searched codebase*

*Updated todo list*

*Searched filesystem*

*Searched filesystem*

*Searched filesystem*

*Searched filesystem*

*Grep searched codebase*

*Updated todo list*

*Viewed [path_visualizer.py](file:///e:/grid/application/resonance/path_visualizer.py) *

*Viewed [router.py](file:///e:/grid/application/resonance/api/router.py) *

*Viewed [type_validator.py](file:///e:/grid/python/type_validator.py) *

*Viewed [test_rag.py](file:///e:/grid/tests/test_rag.py) *

*Updated todo list*

### Planner Response

# Master Plan: Simplify & Optimize Directory Structure (Non‑Breaking)

You have **multiple “package roots”** that overlap in names and purpose, which creates import ambiguity and type-checker chaos:

- **Duplicate project root:** [light_of_the_seven/](file:///e:/grid/light_of_the_seven:0:0-0:0) is effectively a *second copy* of the repo (it contains [application/](file:///e:/grid/application:0:0-0:0), [grid/](file:///e:/grid/grid:0:0-0:0), [tools/](file:///e:/grid/tools:0:0-0:0), [src/](file:///e:/grid/src:0:0-0:0), etc.).
- **Two GRID cores:** [grid/](file:///e:/grid/grid:0:0-0:0) (top-level package) and [src/grid/](file:///e:/grid/src/grid:0:0-0:0) (another implementation) both exist and are imported (`from src.grid...` in tests).
- **Confusing generic names at repo root:** [models/](file:///e:/grid/models:0:0-0:0), [tools/](file:///e:/grid/tools:0:0-0:0), [core/](file:///e:/grid/core:0:0-0:0), [python/](file:///e:/grid/light_of_the_seven/python:0:0-0:0) are all importable top-level packages and can easily collide with other [models/](file:///e:/grid/models:0:0-0:0) and [tools/](file:///e:/grid/tools:0:0-0:0) inside other roots.
- **A non-Python [mothership/](file:///e:/grid/mothership:0:0-0:0) directory** exists at repo root (Node assets), while the Python backend is [application/mothership/](file:///e:/grid/application/mothership:0:0-0:0).

Your [.cursor/rules/project_structure.md](file:///e:/grid/.cursor/rules/project_structure.md:0:0-0:0) already describes the intended canonical layout: [grid/](file:///e:/grid/grid:0:0-0:0), [light_of_the_seven/](file:///e:/grid/light_of_the_seven:0:0-0:0), [tools/](file:///e:/grid/tools:0:0-0:0), [application/](file:///e:/grid/application:0:0-0:0), etc. The problem is that **your current [light_of_the_seven/](file:///e:/grid/light_of_the_seven:0:0-0:0) directory violates this by duplicating the entire root**.

Below is a plan that’s “smart and clever” in practice: **canonicalize one source-of-truth layout**, and use **compatibility shims + incremental migration** to avoid breaking functionality.

---

## 0) Non‑Negotiable Goal (Invariant)
- **All existing import paths continue to work** during the migration period (weeks/months), via:
  - compatibility packages ([__init__.py](file:///e:/grid/core/__init__.py:0:0-0:0) forwarding),
  - minimal wrapper modules,
  - controlled `sys.path` only in legacy scripts/tests (and then removed).

---

# Phase 1 — Declare Canonical Roots (Source of Truth)

## 1.1 Canonical Python package roots (what “wins”)
- **Keep** [grid/](file:///e:/grid/grid:0:0-0:0) as the canonical core package (already aligns with docs + CLI `python -m grid ...`)
- **Keep** [application/](file:///e:/grid/application:0:0-0:0) as application layer (`application.mothership`, `application.resonance`)
- **Keep** [tools/](file:///e:/grid/tools:0:0-0:0) as dev tooling (`tools.rag` etc.)
- **Keep** [light_of_the_seven/](file:///e:/grid/light_of_the_seven:0:0-0:0) as cognitive/research **ONLY** (not a second repo root)

### Why this matches GRID principles
- **Layering:** [grid/](file:///e:/grid/grid:0:0-0:0) (core), [application/](file:///e:/grid/application:0:0-0:0) (orchestration/API), [tools/](file:///e:/grid/tools:0:0-0:0) (aux tooling), [light_of_the_seven/](file:///e:/grid/light_of_the_seven:0:0-0:0) (cognitive layer).
- **Local-first:** tools remain optional (RAG, LLM adapters), applications can degrade gracefully.

---

# Phase 2 — Remove the Biggest Source of Confusion: [light_of_the_seven/](file:///e:/grid/light_of_the_seven:0:0-0:0) as a Duplicate Repo

## 2.1 Current issue
You currently have:
- `e:\grid\light_of_the_seven\application\mothership\...`
- `e:\grid\light_of_the_seven\tools\...`
- `e:\grid\light_of_the_seven\grid\...`

These are *shadow copies* of your canonical packages. Depending on `PYTHONPATH`/editor config, imports can resolve to the wrong copy.

## 2.2 Target for [light_of_the_seven/](file:///e:/grid/light_of_the_seven:0:0-0:0)
Make [light_of_the_seven/](file:///e:/grid/light_of_the_seven:0:0-0:0) contain only:
- `light_of_the_seven/cognitive_layer/...` (schemas, decision support, etc.)
- (optionally) `light_of_the_seven/research/...` for papers/notes/experiments
- (optionally) `light_of_the_seven/examples/...` that explicitly import canonical packages

### What to do with the duplicated subtrees
- **Move** these duplicated folders into an archival namespace that is NOT importable:
  - `light_of_the_seven/_mirror/` or `light_of_the_seven/_legacy_mirror/`
- Ensure `_mirror` has **no [__init__.py](file:///e:/grid/core/__init__.py:0:0-0:0)** and is excluded from type checking / tooling.

This gives you:
- clean navigation
- no accidental imports
- zero runtime impact if nothing imports those mirrored modules directly

---

# Phase 3 — Resolve the [grid/](file:///e:/grid/grid:0:0-0:0) vs [src/grid/](file:///e:/grid/src/grid:0:0-0:0) Split (Second Biggest Confusion)

## 3.1 Current issue
- Tests and some code import `src.grid.*`:
  - `from src.grid.pattern.engine import PatternEngine`
- Core code imports `grid.*`:
  - `from grid.application import IntelligenceApplication`

This is a classic “two codebases” problem.

## 3.2 Canonical decision
Pick **one** as canonical. Given your docs and CLI, the canonical should be:

- **Canonical:** [grid/](file:///e:/grid/grid:0:0-0:0)
- **Legacy / transitional:** [src/](file:///e:/grid/src:0:0-0:0)

## 3.3 Migration strategy (non-breaking)
- Keep [src/](file:///e:/grid/src:0:0-0:0) for now, but **turn it into a thin compatibility layer**:
  - `src/grid/...` modules should eventually re-export from `grid/...`
  - Example end state:
    - [src/grid/pattern/engine.py](file:///e:/grid/src/grid/pattern/engine.py:0:0-0:0) becomes a shim: imports `from grid.patterns...` (or wherever you place the canonical engine)
- Then update tests to import `grid.*` instead of `src.grid.*` gradually.

This can be done module-by-module without breaking anything.

---

# Phase 4 — Fix Generic Top-Level Name Collisions ([models](file:///e:/grid/models:0:0-0:0), [core](file:///e:/grid/core:0:0-0:0), [python](file:///e:/grid/light_of_the_seven/python:0:0-0:0))

## 4.1 Root-level [models/](file:///e:/grid/models:0:0-0:0) package
It’s actively used ([SEGA/orchestrator.py](file:///e:/grid/SEGA/orchestrator.py:0:0-0:0) imports `from models import ...`).

### Target
- Rename [models/](file:///e:/grid/models:0:0-0:0) to something unique and semantically meaningful, e.g.:
  - `sega_models/` or `mythic_models/` or `dragon_models/`

### Non-breaking method
- Keep a **compatibility [models/](file:///e:/grid/models:0:0-0:0) package** that only re-exports from the new package, then deprecate later.
  - This avoids breaking [SEGA/orchestrator.py](file:///e:/grid/SEGA/orchestrator.py:0:0-0:0).

## 4.2 Root-level [core/](file:///e:/grid/core:0:0-0:0) package
Also used (`from core.products import Product`).

### Target
- Rename [core/](file:///e:/grid/core:0:0-0:0) → `grid_core/` or `sega_core/` (depending on intended ownership)
- Provide a compatibility [core/](file:///e:/grid/core:0:0-0:0) wrapper package during transition.

## 4.3 Root-level [python/](file:///e:/grid/light_of_the_seven/python:0:0-0:0) directory
This is dangerously generic: people assume it’s “scripts”, but it’s importable.

### Target
- Rename [python/](file:///e:/grid/light_of_the_seven/python:0:0-0:0) → `scripts_py/` (not importable) **or**
- Convert it into a proper package under a unique name: `grid_devtools/`

Given your code ([python/type_validator.py](file:///e:/grid/python/type_validator.py:0:0-0:0) imports `light_of_the_seven.cognitive_layer.schemas`), it’s mostly tooling/scripts. Prefer:
- [scripts/](file:///e:/grid/light_of_the_seven/scripts:0:0-0:0) (already exists) or `dev/` directory.

---

# Phase 5 — Rename the Node [mothership/](file:///e:/grid/mothership:0:0-0:0) folder to avoid confusion
You have:
- [application/mothership](file:///e:/grid/application/mothership:0:0-0:0) (Python FastAPI backend)
- [mothership/](file:///e:/grid/mothership:0:0-0:0) (Node assets)

### Target
Rename the Node folder to:
- `mothership_ui/` or `mothership_frontend/`

This is low-risk and massively reduces confusion for developers.

---

# Phase 6 — Standardize Import Policy (Enforceable Rule)
You already have a rule doc saying “absolute imports”. Extend that into an executable rule:

## 6.1 Canonical import forms
- **Core:** `from grid...`
- **Apps:** `from application.mothership...`
- **Tools:** `from tools.rag...`
- **Cognitive layer:** `from light_of_the_seven.cognitive_layer...`

## 6.2 Forbidden patterns (to phase out)
- `from src...` (unless it’s a compatibility shim)
- `from models...`, `from core...` (unless compatibility period)
- any `sys.path.insert(...)` except inside explicit legacy test harnesses

---

# Phase 7 — Tooling / Type Checker Alignment (prevent “wrong copy imported”)
Even if runtime works, editors/type checkers get confused if they see multiple roots.

## 7.1 basedpyright/pyright configuration
Right now there’s no `pyrightconfig.json`. Plan:
- Add `pyrightconfig.json` (or basedpyright section in [pyproject.toml](file:///e:/grid/pyproject.toml:0:0-0:0)) to:
  - explicitly define `include` roots,
  - explicitly `exclude` `light_of_the_seven/_mirror/**`, `archival/**`, and large irrelevant trees.
- Ensure only the canonical root is analyzed.

(We will do this only after you approve the plan.)

---

# Phase 8 — Execution Order (Safe, Incremental)

## Step-by-step rollout (no breakage)
1. **Quarantine mirror repo**
   - Move [light_of_the_seven/application](file:///e:/grid/light_of_the_seven/application:0:0-0:0), [light_of_the_seven/tools](file:///e:/grid/light_of_the_seven/tools:0:0-0:0), [light_of_the_seven/grid](file:///e:/grid/light_of_the_seven/grid:0:0-0:0), etc. → `light_of_the_seven/_mirror/`
2. **Rename Node mothership**
   - [mothership/](file:///e:/grid/mothership:0:0-0:0) → `mothership_frontend/`
3. **Introduce compatibility shims**
   - `src/grid/*` re-export from `grid/*` gradually
   - [models/](file:///e:/grid/models:0:0-0:0) re-export from `sega_models/` (after rename)
   - [core/](file:///e:/grid/core:0:0-0:0) re-export from `sega_core/` (after rename)
4. **Update imports in first-party code**
   - Prioritize: runtime entrypoints + FastAPI apps + tools/rag + tests
5. **Update tests**
   - Migrate `from src.grid...` → `from grid...`
6. **Add type-checker excludes**
   - Ensure the mirror dirs don’t pollute analysis

---

# Validation Checklist (must pass before each migration step is “done”)
- **Smoke imports**
  - `python -c "import grid; import application.mothership; import tools.rag"`
- **Unit tests**
  - `pytest tests/`
- **Type check**
  - `basedpyright .` (after excludes)
- **Runtime**
  - [python -m application.mothership.main](file:///e:/grid/SEGA/orchestrator.py:85:0-104:39) (start server)
  - Call one endpoint (health/ping)

---

# Key mismatches & bad structures identified (concrete)
- **Duplicate repo root:** [light_of_the_seven/](file:///e:/grid/light_of_the_seven:0:0-0:0) contains its own [grid/](file:///e:/grid/grid:0:0-0:0), [tools/](file:///e:/grid/tools:0:0-0:0), [application/](file:///e:/grid/application:0:0-0:0)
- **Dual grid implementations:** [grid/](file:///e:/grid/grid:0:0-0:0) vs [src/grid/](file:///e:/grid/src/grid:0:0-0:0)
- **Duplicate tools:** [tools/](file:///e:/grid/tools:0:0-0:0) and [light_of_the_seven/tools/](file:///e:/grid/light_of_the_seven/tools:0:0-0:0) both define [tools](file:///e:/grid/tools:0:0-0:0) package
- **Generic root packages:** [models/](file:///e:/grid/models:0:0-0:0), [core/](file:///e:/grid/core:0:0-0:0), [python/](file:///e:/grid/light_of_the_seven/python:0:0-0:0) are ambiguous and conflict-prone
- **Naming collision:** [mothership/](file:///e:/grid/mothership:0:0-0:0) folder name conflicts with the Python backend package name conceptually

---

# Two Clarifying Questions (so the plan won’t break anything)
1. **Is [light_of_the_seven/](file:///e:/grid/light_of_the_seven:0:0-0:0) intended to be a standalone installable package**, or just a submodule inside this repo?
   - If standalone, we’ll keep its internal [setup.py](file:///e:/grid/light_of_the_seven/light_of_the_seven/setup.py:0:0-0:0)/[src/](file:///e:/grid/src:0:0-0:0) layout but still remove the duplicate `grid/application/tools` mirrors.
2. **Is [src/](file:///e:/grid/src:0:0-0:0) intended to become the canonical home eventually (src-layout packaging)**, or is it legacy?
   - Your current tooling/docs suggest [grid/](file:///e:/grid/grid:0:0-0:0) is canonical, but I want your confirmation before we choose.

---

## Confirm before implementation
If you confirm:
- the canonical roots ([grid/](file:///e:/grid/grid:0:0-0:0), [application/](file:///e:/grid/application:0:0-0:0), [tools/](file:///e:/grid/tools:0:0-0:0), [light_of_the_seven/cognitive_layer](file:///e:/grid/light_of_the_seven/cognitive_layer:0:0-0:0)),
- and that we can quarantine [light_of_the_seven](file:///e:/grid/light_of_the_seven:0:0-0:0)’s mirrored subtrees,

…then I’ll produce an **implementation PR-style checklist** (exact moves, exact shims, exact import rewrites) and start making changes incrementally with validation at each step.

### User Input

1. Analysis of Clarifying Questions**
The plan sought direction on two critical questions:

### **Question 1: Is `light_of_the_seven/` intended to be a standalone installable package, or just a submodule inside this repo?**
#### **Project Context**
- The `.cursorrules` explicitly state:
  > "GRID is a **Python-based framework** for exploring complex systems through geometric resonance patterns. It combines:
  > - Layered architecture (core, API, database, CLI, services)
  > - **Cognitive decision support layer (`light_of_the_seven/cognitive_layer/`)**
  > - Local-only RAG system (`tools/rag/`) using Ollama models
  > - Pattern recognition using 9 cognition patterns
  > - Event-driven processing pipeline"

- The `light_of_the_seven/` directory is described as the **cognitive architecture and research** layer, not a standalone package.
- The `.cursorrules` also emphasize:
  > "Respect module boundaries and separation of concerns."

#### **Current State**
- `light_of_the_seven/` currently contains:
  - A **duplicate** of the entire repo (`grid/`, `tools/`, `application/`, etc.).
  - A `cognitive_layer/` subdirectory (the intended purpose).
  - A `setup.py` file, suggesting it was **historically** treated as a standalone package.

#### **Correct Direction**
- **`light_of_the_seven/` should NOT be a standalone package.**
  - It is a **submodule** of the GRID project, specifically for the **cognitive layer**.
  - The `cognitive_layer/` subdirectory is the **only** part that should remain importable.
  - The duplicate `grid/`, `tools/`, and `application/` directories inside `light_of_the_seven/` should be **quarantined** (moved to `_mirror/` or `_legacy/`).
  - The `setup.py` file should be **removed or archived** (unless it is used for legacy purposes).

---

### **Question 2: Is `src/` intended to become the canonical home eventually (src-layout packaging), or is it legacy?**
#### **Project Context**
- The `.cursorrules` state:
  > "Follow layered architecture: **core → API → database → CLI → services**."
  - The **canonical core package** is `grid/`, not `src/grid/`.
  - The `src/` directory is **not mentioned** in the `.cursorrules`, suggesting it is **not part of the intended architecture**.

- The `.cursorrules` also emphasize:
  > "Use absolute imports for project modules."

#### **Current State**
- `src/grid/` contains a **second implementation** of the `grid` package.
- Some tests and modules import from `src.grid.*` instead of `grid.*`.
- This creates **ambiguity** and violates the **single source of truth** principle.

#### **Correct Direction**
- **`src/` is legacy and should NOT become the canonical home.**
  - The **canonical home** for the `grid` package is `grid/`.
  - `src/grid/` should be **converted into a compatibility layer** that re-exports from `grid/`.
  - Over time, imports should be updated to use `from grid...` instead of `from src.grid...`.
  - The `src/` directory should eventually be **deprecated and removed**.

---

## **2. Alignment with GRID Principles**
The proposed direction aligns with the following **GRID principles**:

### **1. Local-First Operation**
- The plan **avoids external dependencies** and ensures all changes are **local to the project**.
- The RAG system (`tools/rag/`) remains **local-only** (ChromaDB + Ollama models).

### **2. Layered Architecture**
- The **canonical roots** (`grid/`, `application/`, `tools/`, `light_of_the_seven/cognitive_layer/`) respect the **layered architecture**:
  - `grid/`: Core intelligence layer.
  - `application/`: Application-specific logic (e.g., `mothership`).
  - `tools/`: Auxiliary tooling (e.g., RAG, LLM adapters).
  - `light_of_the_seven/cognitive_layer/`: Cognitive decision support.

### **3. Separation of Concerns**
- The plan **eliminates duplicate roots** (e.g., `light_of_the_seven/grid/`, `src/grid/`), ensuring **one source of truth** for each module.
- The `cognitive_layer/` is **isolated** in `light_of_the_seven/`, as intended.

### **4. Non-Breaking Migration**
- The plan uses **compatibility shims** (e.g., `src/grid/` re-exports from `grid/`) to ensure **runtime behavior remains unchanged**.
- The **quarantine** of duplicate directories (`_mirror/`) ensures **no accidental imports**.

### **5. Type Safety and Tooling**
- The plan **excludes legacy paths** from type checking (e.g., `_mirror/`, `archival/`), reducing noise in `basedpyright` diagnostics.
- The **canonical imports** resolve ambiguity in type-checking errors (e.g., `grid.api.routers` vs `src.grid.api.routers`).

---

## **3. Updated Plan with Correct Direction**
### **Phase 1: Canonicalize `light_of_the_seven/`**
1. **Quarantine duplicates**:
   - Move `light_of_the_seven/grid/`, `light_of_the_seven/tools/`, `light_of_the_seven/application/` → `light_of_the_seven/_mirror/`.
   - Ensure `_mirror/` has **no `__init__.py`** and is **excluded from type checking**.
2. **Retain only `cognitive_layer/`**:
   - Keep `light_of_the_seven/cognitive_layer/` as the **only importable submodule**.
3. **Archive `setup.py`**:
   - Move `light_of_the_seven/setup.py` → `light_of_the_seven/_mirror/setup.py` (or delete if unused).

### **Phase 2: Resolve `grid/` vs `src/grid/` Split**
1. **Make `src/grid/` a compatibility layer**:
   - Update `src/grid/__init__.py` to re-export from `grid/`:
     ```python
     from grid import *  # Re-export all canonical modules
     ```
2. **Update imports in tests and legacy code**:
   - Replace `from src.grid...` → `from grid...` **incrementally**.
3. **Deprecate `src/`**:
   - Add a **deprecation warning** in `src/grid/__init__.py`:
     ```python
     import warnings
     warnings.warn("src.grid is deprecated. Use 'grid' instead.", DeprecationWarning)
     ```

### **Phase 3: Rename Generic Root Packages**
1. **Rename `models/` → `sega_models/`**:
   - Add a compatibility shim in `models/__init__.py`:
     ```python
     from sega_models import *  # Re-export from the new package
     ```
2. **Rename `core/` → `sega_core/`**:
   - Add a compatibility shim in `core/__init__.py`:
     ```python
     from sega_core import *  # Re-export from the new package
     ```
3. **Rename `light_of_the_seven/python/` → `light_of_the_seven/scripts/`**:
   - Move scripts to `light_of_the_seven/scripts/` (non-importable).

### **Phase 4: Rename Node `mothership/` Folder**
- Rename `mothership/` → `mothership_frontend/` to avoid confusion with `application/mothership/`.

### **Phase 5: Fix Diagnostics in Canonical Modules**
1. **Install missing dependencies**:
   ```bash
   pip install redis sqlalchemy manim openai sentence-transformers google-generativeai plotly networkx icalendar
   ```
2. **Fix import paths**:
   - Example: `from grid.api.routers` → `from application.mothership.api.routers`.
3. **Fix type mismatches**:
   - Example: `List[float]` → `Dict[str, float]`.
4. **Fix attribute access errors**:
   - Example: Add `api_keys: Dict[str, str]` to `StateStore`.
5. **Fix undefined variables**:
   - Example: Import `Quantizer` from `grid.quantization`.

### **Phase 6: Validation**
1. **Smoke imports**:
   ```bash
   python -c "import grid; import application.mothership; import tools.rag; import light_of_the_seven.cognitive_layer"
   ```
2. **Type checking**:
   ```bash
   basedpyright .
   ```
3. **Unit tests**:
   ```bash
   pytest tests/
   ```
4. **Runtime testing**:
   ```bash
   python -m application.mothership.main
   ```

### **Phase 7: Automation**
1. **Remove unused imports**:
   ```bash
   autoflake --remove-all-unused-imports -i -r .
   ```
2. **Sort imports**:
   ```bash
   isort .
   ```
3. **Linting**:
   ```bash
   ruff check .
   ```

---

## **4. Key Decisions Summary**
| Question | Correct Direction | Rationale |
|----------|-------------------|-----------|
| Is `light_of_the_seven/` a standalone package? | **No**, it is a submodule for `cognitive_layer/`. | Aligns with `.cursorrules` (cognitive layer is part of GRID, not standalone). |
| Is `src/` the canonical home? | **No**, `grid/` is canonical. `src/` is legacy. | `.cursorrules` specify `grid/` as the core package. |
| How to handle duplicate directories? | **Quarantine** duplicates in `_mirror/`. | Ensures no accidental imports while preserving history. |
| How to handle generic root packages? | **Rename** to unique names (e.g., `sega_models/`). | Avoids ambiguity and aligns with layered architecture. |

---

## **5. Next Steps**
1. **Approve the canonical structure**:
   - `grid/` (core), `application/` (apps), `tools/` (auxiliary), `light_of_the_seven/cognitive_layer/` (cognitive).
2. **Approve the quarantine of `light_of_the_seven` duplicates**:
   - Move `grid/`, `tools/`, `application/` → `light_of_the_seven/_mirror/`.
3. **Approve the deprecation of `src/`**:
   - Convert `src/grid/` into a compatibility layer.
4. **Prioritize diagnostics fixes**:
   - Start with **missing imports** and **attribute access errors** in canonical modules.

*Updated todo list*

*Listed directory [light_of_the_seven](file:///e:/grid/light_of_the_seven) *

### Planner Response

I’m going to do two quick checks before we start moving/rewiring anything (to keep this non-breaking): (1) verify where the *real* cognitive layer code actually lives (your top-level [light_of_the_seven/cognitive_layer](file:///e:/grid/light_of_the_seven/cognitive_layer:0:0-0:0) looks empty right now), and (2) inspect [src/grid](file:///e:/grid/src/grid:0:0-0:0) to see whether it can truly be shimmed to [grid/](file:///e:/grid/grid:0:0-0:0) or whether it’s a distinct legacy implementation that needs a staged port. I’ll also look at your `.vscode/launch.json` because launch `cwd`/`PYTHONPATH` is a common cause of “imports resolve to the wrong duplicate tree.”

*Viewed [launch.json](file:///e:/grid/.vscode/launch.json) *

*Listed directory [cognitive_layer](file:///e:/grid/light_of_the_seven/cognitive_layer) *

*Searched filesystem*

*Viewed [engine.py](file:///e:/grid/src/grid/pattern/engine.py) *

*Viewed [database.py](file:///e:/grid/src/grid/persistence/database.py) *

### Planner Response

# Confirmed Decisions (Aligned)
- **[light_of_the_seven/](file:///e:/grid/light_of_the_seven:0:0-0:0) is not standalone** in this repo’s “canonical runtime” sense; it should function as the **cognitive layer subtree**, not a second repo root.
- **[grid/](file:///e:/grid/grid:0:0-0:0) is canonical**; **[src/](file:///e:/grid/light_of_the_seven/src:0:0-0:0) is legacy** and should eventually be deprecated or turned into a shim.

# Two Important Implementation Caveats I Found
## 1) [light_of_the_seven/cognitive_layer/](file:///e:/grid/light_of_the_seven/cognitive_layer:0:0-0:0) exists but appears empty
Right now `e:\grid\light_of_the_seven\cognitive_layer\...` has the right folder layout, but no files were listed inside the subpackages.

At the same time, there are *multiple other* [schemas/](file:///e:/grid/light_of_the_seven/schemas:0:0-0:0) locations under that duplicate tree, including:
- [e:\grid\light_of_the_seven\light_of_the_seven\cognitive_layer\schemas\](file:///e:/grid/light_of_the_seven/light_of_the_seven/cognitive_layer/schemas:0:0-0:0)
- [e:\grid\light_of_the_seven\src\light_of_the_seven\schemas\](file:///e:/grid/light_of_the_seven/src/light_of_the_seven/schemas:0:0-0:0)
- and others

So before we “quarantine the duplicate repo,” we need to decide **which of those is the real source-of-truth cognitive schemas** (so we don’t accidentally quarantine the only real implementation).

## 2) [src/grid](file:///e:/grid/src/grid:0:0-0:0) can’t be shimmed with a simple `src/grid/__init__.py`
[src/grid](file:///e:/grid/src/grid:0:0-0:0) is currently working as a **namespace-package style tree** (no [__init__.py](file:///e:/grid/grid/__init__.py:0:0-0:0) in [src/](file:///e:/grid/light_of_the_seven/src:0:0-0:0) or [src/grid/](file:///e:/grid/src/grid:0:0-0:0) or [src/grid/pattern/](file:///e:/grid/src/grid/pattern:0:0-0:0)). If we add `src/grid/__init__.py` without converting subdirs too, imports like `src.grid.pattern.engine` can break.

Also, `src/grid/*` looks like a **minimal legacy/test implementation** (not a 1:1 mirror of `grid/*`), so “re-export everything from [grid](file:///e:/grid/grid:0:0-0:0)” isn’t mechanically true yet.

# What I Recommend Doing Next (Non-Breaking Order)
## Phase A (safe, immediate): tooling guardrails first
- **Add type-checker excludes** so basedpyright/pyright stop indexing the duplicated subtrees under `e:\grid\light_of_the_seven\...` (but keep whatever we decide is the canonical cognitive layer).
- This reduces import ambiguity *immediately* without moving files yet.

## Phase B (requires approval): quarantine the duplicate repo content
- Create `e:\grid\light_of_the_seven\_mirror\`
- Move duplicated roots like:
  - [e:\grid\light_of_the_seven\application\](file:///e:/grid/light_of_the_seven/application:0:0-0:0)
  - `...\grid\`
  - `...\tools\`
  - `...\tests\`
  - `...\src\`
  - etc.
- Leave behind only the canonical cognitive layer subtree.

This involves **destructive filesystem moves**, so I’ll only do it after you explicitly approve.

## Phase C: handle [src/](file:///e:/grid/light_of_the_seven/src:0:0-0:0) deprecation correctly
- First, decide whether [src/grid](file:///e:/grid/src/grid:0:0-0:0) should be:
  - **Deprecated but kept** (tests updated to stop using it), or
  - **Ported into [grid/](file:///e:/grid/grid:0:0-0:0)** (real migration), then replaced with shims.
- Only after we have canonical equivalents do we implement re-exports.

# Two Quick Yes/No Questions (so I can proceed safely)
1. **Cognitive layer source-of-truth:** should `light_of_the_seven.cognitive_layer` come from:
   - [e:\grid\light_of_the_seven\cognitive_layer\](file:///e:/grid/light_of_the_seven/cognitive_layer:0:0-0:0) (populate it by moving files in), or
   - do you want to keep using the nested implementation (and we “promote” it)?
2. **Approval to move directories:** do you want me to proceed with the **physical quarantine** (Move-Item operations) once we identify the canonical cognitive layer files?

# Status
- **Plan is now approved in principle** (your clarifications are consistent with the repo’s stated architecture).
- **Next action pending your two answers above**, then I’ll implement Phase A immediately and prepare Phase B moves with a rollback-friendly sequence.
