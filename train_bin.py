import os

import torch
import torchvision
import torchvision.datasets as datasets
import torchvision.transforms as transforms
import torch.optim as optim
import torch.utils.data
import torch.nn as nn

import helper
import model
import mlflow
from tqdm import tqdm

#----------------------
pick_model = model.Vae_var()

def show_scatter(lat = 2) :
    helper.show_scatter_lat_mu_sigma(examples=10000, model_loaded=pick_model, lat=lat,in_train_class=True)

#---------------------=
# pg_ctl -D /Users/dominikocsofszki/PycharmProjects/mlp/sql/sql1 -l logfile start
# mlflow server --backend-store-uri postgresql://mlflow@localhost/mlflow_db --default-artifact-root file:"/Users/dominikocsofszki/PycharmProjects/mlp/mlruns" -h 0.0.0.0 -p 8000
# DEBUG PARAMS:
TEST_ONLY_LAST = True
TEST_AFTER_EPOCH = 11
COUNT_PRINTS = 5
EPOCHS = 200
SHOW_SCATTER_EVERY = 2

#
# LR_RATE = 3e-4
BATCH_SIZE = 16 * 2 ** 1
LR_RATE = 3e-4
ADD_TEXT = ''
RUN_SAVE_NAME = pick_model.__class__.__name__ + str(ADD_TEXT)
print(f'{RUN_SAVE_NAME = }')
HAS_LOSS_FUNCTION = True  # TODO If model has loss function implemented
os.environ['MLFLOW_TRACKING_URI'] = 'http://localhost:8000/'  # TODO Use this for SQL \ Delete for using local
# with mlflow.start_run(run_name=pick_model.__class__.__name__):
with mlflow.start_run(run_name=RUN_SAVE_NAME):
    print(f'{EPOCHS = }')
    # for x in pick_model.parameters():
    #     print(x.shape)
    # print(list(pick_model.parameters()))
    # MOMENTUM = 0.9
    # BATCH_SIZE = 32 * 2 ** 1
    print(f'{BATCH_SIZE = }')
    pick_device = 'cpu'
    DEVICE = torch.device(pick_device)  # alternative 'mps' - but no speedup...
    model = pick_model.to(DEVICE)
    print('its needed:')

    print(60000 / BATCH_SIZE)

    mlflow.log_param('epochs', EPOCHS)
    mlflow.log_param('LR_RATE', LR_RATE)
    # mlflow.log_param('MOMENTUM', MOMENTUM)
    mlflow.log_param('batch_size', BATCH_SIZE)
    mlflow.log_param('pick_device', pick_device)
    model_entries = [entry for entry in model.modules()]  ##need to ignore other files!?!?<<<<<<<<
    print(f'{model_entries.__len__()}')
    mlflow.log_param('model_name_full', model.__class__)
    mlflow.log_param('model_name', model.__class__.__name__)
    # ------------------TRACKING-----------------------

    # Downloading the dataset
    trainset = datasets.MNIST(root='data/dataset', train=True, transform=transforms.ToTensor(), download=True)
    testset = datasets.MNIST(root='data/testset', train=False, transform=transforms.ToTensor(),
                             download=True)  # TODO use train3!!!
    # assert False #TODO do not use testset is missing train=False! For comparing here

    # Filter for only two classes #TODO Not sure yet if it is needed

    # Trainloader
    trainloader = torch.utils.data.DataLoader(trainset, batch_size=BATCH_SIZE)  # No shuffle for reproducibility
    testsetloader = torch.utils.data.DataLoader(testset, batch_size=BATCH_SIZE)


    loss_arr = []
    test_img_after_epochs = []
    optimizer = torch.optim.Adam(model.parameters(), lr=LR_RATE)
    loss_fn = nn.BCELoss(reduction='sum')
    for epoch in range(EPOCHS):

        loop = tqdm(enumerate(trainloader))
        for i, (x, _) in loop:
            # forward pass
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
            loop.set_postfix(loss=loss.item(), loss_avg=loss.item()/BATCH_SIZE)
            loss_arr.append(loss.item())
            # loop.set_postfix(loss_avg=loss.item()/BATCH_SIZE)
        if epoch %  SHOW_SCATTER_EVERY== 0:
            show_scatter()
    # mlflow.log_param('acc_arr', acc_arr)
    # mlflow.log_param('accuracy', accuracy)
    # mlflow.log_param('avg_loss', avg_loss)

    show_scatter()
    print('finish!!!')

    # SAVE_NAME_MODEL = model.__class__.__name__ + '_weights'
    SAVE_NAME_MODEL = RUN_SAVE_NAME + '_weights'
    # PATH = '/Users/dominikocsofszki/PycharmProjects/mlp/data/weights/weights_training'
    # PATH = '/Users/dominikocsofszki/PycharmProjects/mlp/data/weights/weights_model_classifier_soft'
    PATH = '/Users/dominikocsofszki/PycharmProjects/mlp/data/weights/' + SAVE_NAME_MODEL

    print(f'save weights at {PATH = }')
    print(f'{PATH = }')
    torch.save(model.state_dict(), PATH)
