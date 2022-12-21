import os

import torch.utils.data
import torch.nn as nn

import helper
import model
import mlflow
from tqdm import tqdm
from MyDataSet import MyDataSets
##############################################################################################################
##############################################################################################################
start_database_terminal = 'pg_ctl -D /Users/dominikocsofszki/PycharmProjects/mlp/sql/sql1 -l logfile start'
start_mlflow_server ='mlflow server --backend-store-uri postgresql://mlflow@localhost/mlflow_db --default-artifact-root file:"/Users/dominikocsofszki/PycharmProjects/mlp/mlruns" -h 0.0.0.0 -p 8000'
##############################################################################################################
##############################################################################################################
def mlflow_start_log_first(EPOCHS,LR_RATE,BATCH_SIZE,pick_device,model) :
    print(f'{BATCH_SIZE = }')
    mlflow.log_param('epochs', EPOCHS)
    mlflow.log_param('LR_RATE', LR_RATE)
    # mlflow.log_param('MOMENTUM', MOMENTUM)
    mlflow.log_param('batch_size', BATCH_SIZE)
    mlflow.log_param('pick_device', pick_device)
    mlflow.log_param('model_name_full', model.__class__)
    mlflow.log_param('model_name', model.__class__.__name__)
##############################################################################################################
##############################################################################################################
def show_scatter(model, mydataset, current_epoch='epoch_information'):
    helper.show_scatter_binary_dataset(model=model, mydataset=mydataset, current_epoch=current_epoch)
    # helper.
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################

pick_model = model.Vae_var_28_28()
BATCH_SIZE = 2 ** 8

use_classes = (4, 9)
MYDATASET = MyDataSets(tuble=use_classes,batch_size_train=BATCH_SIZE)
# DEBUG PARAMS:
TEST_ONLY_LAST = True
TEST_AFTER_EPOCH = 11
COUNT_PRINTS = 5
EPOCHS = 30
SHOW_SCATTER_EVERY = 5

#
# LR_RATE = 3e-4
LR_RATE = 3e-4
ADD_TEXT = ''
RUN_SAVE_NAME = pick_model.__class__.__name__ + str(ADD_TEXT)
print(f'{RUN_SAVE_NAME = }')
HAS_LOSS_FUNCTION = True  # TODO If model has loss function implemented
os.environ['MLFLOW_TRACKING_URI'] = 'http://localhost:8000/'  # TODO Use this for SQL \ Delete for using local
print(f'connecting to: http://localhost:8000/')
print('if not working: open terminal with conda env mlp(source activate mlp):')
print(start_database_terminal)
print(start_mlflow_server)
with mlflow.start_run(run_name=RUN_SAVE_NAME):
    pick_device = 'cpu'
    DEVICE = torch.device(pick_device)  # alternative 'mps' - but no speedup...
    model = pick_model.to(DEVICE)
    mlflow_start_log_first(EPOCHS, LR_RATE, BATCH_SIZE, pick_device, model)

    # ------------------TRACKING-----------------------

    # trainloader = torch.utils.data.DataLoader(MYDATASET.trainset, batch_size=BATCH_SIZE)  # No shuffle for reproducibility
    # testsetloader = torch.utils.data.DataLoader(MYDATASET.testset, batch_size=BATCH_SIZE)
    trainloader = MYDATASET.dataloader_train_full
    testloader = MYDATASET.dataloader_test_full


    loss_arr = []
    test_img_after_epochs = []
    optimizer = torch.optim.Adam(model.parameters(), lr=LR_RATE)
    loss_fn = nn.BCELoss(reduction='sum')
    PRINT_ONCE = True
    for epoch in range(EPOCHS):

        loop = tqdm(enumerate(trainloader))
        for i, (x, _) in loop:
            x = x.to(DEVICE).view(x.shape[0], 28 * 28)  # TODO why?
            x_reconstruction, mu, sigma = model(x)

            reconstruction_loss = loss_fn(x_reconstruction, x)
            kl_div = -torch.sum(
                1 + torch.log(sigma.pow(2)) - mu.pow(2) - sigma.pow(2))  # TODO Search in paper #minus for torch?

            alpha = 0.6
            beta = 1 - alpha

            loss = alpha * reconstruction_loss + beta * kl_div  # TODO Could also change or add alpha,beta weighting!
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            loop.set_postfix(loss=loss.item(), loss_avg=loss.item() / BATCH_SIZE)
            loss_arr.append(loss.item())
            # loop.set_postfix(loss_avg=loss.item()/BATCH_SIZE)
        if epoch % SHOW_SCATTER_EVERY == 0:
            # show_scatter(mydataset=MYDATASET, current_epoch=str(epoch), model=model)
            show_scatter(mydataset=MYDATASET, current_epoch=str(epoch), model=model)
    # mlflow.log_param('acc_arr', acc_arr)
    # mlflow.log_param('accuracy', accuracy)
    # mlflow.log_param('avg_loss', avg_loss)

    show_scatter(mydataset=MYDATASET, model=model, current_epoch=str(epoch))
    print('finish!!!')

    SAVE_NAME_MODEL = RUN_SAVE_NAME + '_weights'
    PATH = '/Users/dominikocsofszki/PycharmProjects/mlp/data/weights/' + SAVE_NAME_MODEL

    print(f'save weights at {PATH = }')
    print(f'{PATH}')
    torch.save(model.state_dict(), PATH)

