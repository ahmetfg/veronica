from . import BINANCE_CRIDENTIALS 
from . import veronica
from . import source
import firebase_admin as fb
from firebase_admin import credentials
from firebase_admin import firestore
import azure.functions as func
import logging

# stateless function for azure cloud
def main(azure_timer: func.TimerRequest) -> None:

    # init firebase admin
    cred = credentials.Certificate("veronica/GCP_CRIDENTIALS.json")
    fb.initialize_app(cred)

    # get exchange client
    client = BINANCE_CRIDENTIALS.Cridentials().client()

    # get firestore client
    db = firestore.client()
    
    # init target pair source
    pair_source = source.Source("DENTUSDT", window = 99)
    
    # init veronica
    broker : veronica.Veronica = veronica.Veronica(source = pair_source, client = client).setLog(3).setSerialize(False)
    
    # init veronicas selected strategy
    broker.strategy_one()

    # fetch bar data and step receptors
    # if fetch succeed
    try:
        # get the last state data
        lastStates = db.collection('datas').document('receptorData').get().to_dict()

        # arrange the receptors with data
        broker.initialize(lastStates)

        # fetch bar data
        pair_source.fetch()

        # fire receptors
        broker.step()

    except Exception as err:
        # log error
        logging.error("step collapsed from:{}".format(err))
        raise err
    
    finally:

        # serialize the new states
        newStates = broker.serialize()

        # save the last state data if its new
        if lastStates != newStates:
            db.collection('datas').document('receptorData').set(newStates)
            logging.info('database refreshed')

        # log bar info
        logging.info("close:{} tsi:{:.2f} stc:{:.2f} at:{}".format(pair_source.close,pair_source.tsi(),pair_source.stoch(),broker.exactIndex))
